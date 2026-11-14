import { handleUpload, type HandleUploadBody } from "@vercel/blob/client";
import { createHmac, timingSafeEqual } from "node:crypto";
import { NextResponse } from "next/server";

const SESSION_COOKIE = "edith_session";
const MAX_UPLOAD_BYTES = 25 * 1024 * 1024;
const ALLOWED_CONTENT_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

class ConfigurationError extends Error {}

function sessionUsername(request: Request): string | null {
  const secret = process.env.AUTH_SECRET;
  if (!secret || secret.length < 32) {
    throw new ConfigurationError("Set AUTH_SECRET to a random value of at least 32 characters.");
  }

  const cookie = request.headers.get("cookie") ?? "";
  const token = cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${SESSION_COOKIE}=`))
    ?.slice(SESSION_COOKIE.length + 1);
  if (!token) return null;

  const [payload, signature] = token.split(".");
  if (!payload || !signature) return null;
  const expected = createHmac("sha256", secret).update(payload).digest("base64url");
  const receivedBytes = Buffer.from(signature);
  const expectedBytes = Buffer.from(expected);
  if (
    receivedBytes.length !== expectedBytes.length ||
    !timingSafeEqual(receivedBytes, expectedBytes)
  ) {
    return null;
  }

  try {
    const decoded = Buffer.from(payload, "base64url").toString("utf8");
    const separator = decoded.lastIndexOf(":");
    const username = decoded.slice(0, separator);
    const expires = Number(decoded.slice(separator + 1));
    if (
      separator < 1 ||
      !/^[a-z0-9_]{3,30}$/.test(username) ||
      !Number.isSafeInteger(expires) ||
      expires < Math.floor(Date.now() / 1000)
    ) {
      return null;
    }
    return username;
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as HandleUploadBody;
    const result = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async (pathname) => {
        const username = sessionUsername(request);
        if (!username) throw new Error("Please sign in again.");
        const parts = pathname.split("/");
        const extension = parts.at(-1)?.split(".").at(-1)?.toLowerCase();
        if (
          parts.length !== 3 ||
          parts[0] !== "edith" ||
          parts[1] !== username ||
          !["pdf", "docx", "txt"].includes(extension ?? "")
        ) {
          throw new Error("Invalid upload path or file type.");
        }
        return {
          allowedContentTypes: ALLOWED_CONTENT_TYPES,
          maximumSizeInBytes: MAX_UPLOAD_BYTES,
          addRandomSuffix: false,
          tokenPayload: JSON.stringify({ username }),
        };
      },
      onUploadCompleted: async ({ blob, tokenPayload }) => {
        if (!tokenPayload) throw new Error("Upload owner was not provided.");
        const payload = JSON.parse(tokenPayload) as { username?: string };
        const username = payload.username;
        if (
          !username ||
          !/^[a-z0-9_]{3,30}$/.test(username) ||
          !blob.pathname.startsWith(`edith/${username}/`)
        ) {
          throw new Error("Uploaded file ownership could not be verified.");
        }
      },
    });
    return NextResponse.json(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not authorize upload.";
    const status = error instanceof ConfigurationError ? 503 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
