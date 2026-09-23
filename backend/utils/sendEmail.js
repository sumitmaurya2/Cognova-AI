import nodemailer from "nodemailer";

const transporter =
  process.env.GMAIL_USER && process.env.GMAIL_APP_PASSWORD
    ? nodemailer.createTransport({
        service: "gmail",
        auth: {
          user: process.env.GMAIL_USER,
          pass: process.env.GMAIL_APP_PASSWORD,
        },
      })
    : null;

export const escapeHtml = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

export const sendEmail = async ({ to, subject, html }) => {
  try {
    if (!transporter)
      throw new Error("GMAIL_USER or GMAIL_APP_PASSWORD is not configured");
    return await transporter.sendMail({
      from: process.env.EMAIL_FROM || process.env.GMAIL_USER,
      to,
      subject,
      html,
    });
  } catch (err) {
    console.error("sendEmail failed:", err.message);
    throw err;
  }
};

export const verificationEmailTemplate = (name, verifyUrl) => `
  <div style="font-family: sans-serif; max-width: 500px; margin: auto;">
    <h2>Hi ${escapeHtml(name)},</h2>
    <p>Thanks for signing up! Please verify your email address by clicking below:</p>
    <a href="${verifyUrl}" style="background:#4f46e5;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">Verify Email</a>
    <p>This link expires in 24 hours. If you didn't create an account, ignore this email.</p>
  </div>
`;

export const resetPasswordEmailTemplate = (name, resetUrl) => `
  <div style="font-family: sans-serif; max-width: 500px; margin: auto;">
    <h2>Hi ${escapeHtml(name)},</h2>
    <p>We received a request to reset your password. Click below to set a new one:</p>
    <a href="${resetUrl}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">Reset Password</a>
    <p>This link expires in 15 minutes. If you didn't request this, ignore this email — your password is safe.</p>
  </div>
`;
