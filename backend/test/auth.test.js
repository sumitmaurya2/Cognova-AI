import test from "node:test";
import assert from "node:assert/strict";
import jwt from "jsonwebtoken";

process.env.JWT_REFRESH_SECRET = "test-refresh-secret";
process.env.GMAIL_USER = "test@example.com";
process.env.GMAIL_APP_PASSWORD = "test-app-password";

const {
  generateRefreshToken,
  clearRefreshTokenCookie,
  sendRefreshTokenCookie,
} = await import("../utils/generateTokens.js");
const { escapeHtml } = await import("../utils/sendEmail.js");

test("refresh tokens carry the user token version", () => {
  const token = generateRefreshToken("user-123", 4);
  const payload = jwt.verify(token, process.env.JWT_REFRESH_SECRET);
  assert.equal(payload.id, "user-123");
  assert.equal(payload.type, "refresh");
  assert.equal(payload.version, 4);
});

test("refresh cookie is HTTP-only and scoped to auth routes", () => {
  const cookies = [];
  const response = {
    cookie: (...args) => cookies.push(args),
    clearCookie: (...args) => cookies.push(args),
  };
  sendRefreshTokenCookie(response, "token");
  assert.equal(cookies[0][0], "refreshToken");
  assert.equal(cookies[0][2].httpOnly, true);
  assert.equal(cookies[0][2].path, "/api/auth");
  clearRefreshTokenCookie(response);
  assert.equal(cookies[1][1].path, "/api/auth");
});

test("email names are escaped before entering HTML", () => {
  assert.equal(
    escapeHtml('<script>alert("x")</script>'),
    "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;",
  );
});
