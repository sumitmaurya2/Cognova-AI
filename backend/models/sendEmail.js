import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export const sendEmail = async ({ to, subject, html }) => {
  try {
    const { data, error } = await resend.emails.send({
      from: process.env.EMAIL_FROM,
      to,
      subject,
      html,
    });

    if (error) {
      console.error("Email send error:", error);
      throw new Error("Email could not be sent");
    }

    return data;
  } catch (err) {
    console.error("sendEmail failed:", err.message);
    throw err;
  }
};

export const verificationEmailTemplate = (name, verifyUrl) => `
  <div style="font-family: sans-serif; max-width: 500px; margin: auto;">
    <h2>Hi ${name},</h2>
    <p>Thanks for signing up! Please verify your email address by clicking below:</p>
    <a href="${verifyUrl}" style="background:#4f46e5;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">Verify Email</a>
    <p>This link expires in 24 hours. If you didn't create an account, ignore this email.</p>
  </div>
`;

export const resetPasswordEmailTemplate = (name, resetUrl) => `
  <div style="font-family: sans-serif; max-width: 500px; margin: auto;">
    <h2>Hi ${name},</h2>
    <p>We received a request to reset your password. Click below to set a new one:</p>
    <a href="${resetUrl}" style="background:#dc2626;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;display:inline-block;">Reset Password</a>
    <p>This link expires in 15 minutes. If you didn't request this, ignore this email — your password is safe.</p>
  </div>
`;