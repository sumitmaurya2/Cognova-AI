import crypto from "crypto";
import jwt from "jsonwebtoken";
import { z } from "zod";
import User from "../models/User.js";
import {
  clearRefreshTokenCookie,
  generateAccessToken,
  generateRefreshToken,
  sendRefreshTokenCookie,
} from "../utils/generateTokens.js";
import {
  sendEmail,
  verificationEmailTemplate,
  resetPasswordEmailTemplate,
} from "../utils/sendEmail.js";

const emailSchema = z.string().trim().toLowerCase().email();
const passwordSchema = z.string().min(8).max(128);
const registerSchema = z.object({
  name: z.string().trim().min(2).max(80),
  email: emailSchema,
  password: passwordSchema,
});
const credentialsSchema = z.object({
  email: emailSchema,
  password: z.string().min(1),
});

const hashToken = (token) =>
  crypto.createHash("sha256").update(token).digest("hex");
const newToken = () => crypto.randomBytes(32).toString("hex");
const tokenExpiry = (minutes) => new Date(Date.now() + minutes * 60 * 1000);
const publicUser = (user) => ({
  id: user._id,
  name: user.name,
  email: user.email,
});
const validationMessage = (error) =>
  error.issues?.[0]?.message || "Invalid request";

const sendVerification = async (user, token) => {
  const verifyUrl = `${process.env.CLIENT_URL}/verify-email?token=${token}`;
  await sendEmail({
    to: user.email,
    subject: "Verify your Cognova account",
    html: verificationEmailTemplate(user.name, verifyUrl),
  });
};

export const register = async (req, res) => {
  try {
    const { name, email, password } = registerSchema.parse(req.body);
    const existingUser = await User.findOne({ email });

    if (existingUser) {
      if (existingUser.isVerified)
        return res.status(409).json({ message: "Email already registered" });
      const token = newToken();
      existingUser.verificationTokenHash = hashToken(token);
      existingUser.verificationTokenExpires = tokenExpiry(24 * 60);
      await existingUser.save();
      await sendVerification(existingUser, token);
      return res
        .status(201)
        .json({ message: "Verification email sent. Please check your inbox." });
    }

    const token = newToken();
    const user = await User.create({
      name,
      email,
      password,
      verificationTokenHash: hashToken(token),
      verificationTokenExpires: tokenExpiry(24 * 60),
    });
    await sendVerification(user, token);
    return res
      .status(201)
      .json({
        message: "Account created. Please check your email to verify it.",
      });
  } catch (error) {
    if (error.name === "ZodError")
      return res.status(400).json({ message: validationMessage(error) });
    if (error.code === 11000)
      return res.status(409).json({ message: "Email already registered" });
    console.error("Registration failed:", error);
    return res
      .status(503)
      .json({
        message: "We could not send the verification email. Please try again.",
      });
  }
};

export const verifyEmail = async (req, res) => {
  try {
    const token = z.string().min(1).parse(req.query.token);
    const user = await User.findOne({
      verificationTokenHash: hashToken(token),
      verificationTokenExpires: { $gt: new Date() },
    });
    if (!user)
      return res
        .status(400)
        .json({ message: "Invalid or expired verification link" });

    user.isVerified = true;
    user.verificationTokenHash = undefined;
    user.verificationTokenExpires = undefined;
    await user.save();
    return res
      .status(200)
      .json({ message: "Email verified successfully. You can now log in." });
  } catch (error) {
    if (error.name === "ZodError")
      return res
        .status(400)
        .json({ message: "A verification token is required" });
    console.error("Email verification failed:", error);
    return res.status(500).json({ message: "Email verification failed" });
  }
};

export const resendVerification = async (req, res) => {
  try {
    const email = emailSchema.parse(req.body.email);
    const user = await User.findOne({ email });
    if (user && !user.isVerified) {
      const token = newToken();
      user.verificationTokenHash = hashToken(token);
      user.verificationTokenExpires = tokenExpiry(24 * 60);
      await user.save();
      await sendVerification(user, token);
    }
    return res
      .status(200)
      .json({
        message: "If that email needs verification, a new link has been sent.",
      });
  } catch (error) {
    if (error.name === "ZodError")
      return res.status(400).json({ message: "Enter a valid email address" });
    console.error("Resend verification failed:", error);
    return res
      .status(503)
      .json({ message: "We could not send the verification email" });
  }
};

export const login = async (req, res) => {
  try {
    const { email, password } = credentialsSchema.parse(req.body);
    const user = await User.findOne({ email }).select("+password");
    if (!user)
      return res.status(401).json({ message: "Invalid email or password" });
    if (user.lockUntil && user.lockUntil > new Date()) {
      return res
        .status(423)
        .json({ message: "Account temporarily locked. Try again later." });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      user.loginAttempts += 1;
      if (user.loginAttempts >= 5) {
        user.lockUntil = new Date(Date.now() + 15 * 60 * 1000);
        user.loginAttempts = 0;
      }
      await user.save();
      return res.status(401).json({ message: "Invalid email or password" });
    }
    if (!user.isVerified)
      return res
        .status(403)
        .json({ message: "Please verify your email before logging in" });

    user.loginAttempts = 0;
    user.lockUntil = undefined;
    user.refreshTokenVersion += 1;
    await user.save();
    sendRefreshTokenCookie(
      res,
      generateRefreshToken(user._id, user.refreshTokenVersion),
    );
    return res
      .status(200)
      .json({
        accessToken: generateAccessToken(user._id),
        user: publicUser(user),
      });
  } catch (error) {
    if (error.name === "ZodError")
      return res.status(400).json({ message: validationMessage(error) });
    console.error("Login failed:", error);
    return res.status(500).json({ message: "Login failed" });
  }
};

export const forgotPassword = async (req, res) => {
  const genericMessage = "If that email exists, a reset link has been sent.";
  try {
    const email = emailSchema.parse(req.body.email);
    const user = await User.findOne({ email });
    if (!user) return res.status(200).json({ message: genericMessage });

    const token = newToken();
    user.resetPasswordTokenHash = hashToken(token);
    user.resetPasswordTokenExpires = tokenExpiry(15);
    await user.save();
    const resetUrl = `${process.env.CLIENT_URL}/reset-password?token=${token}`;
    await sendEmail({
      to: user.email,
      subject: "Reset your Cognova password",
      html: resetPasswordEmailTemplate(user.name, resetUrl),
    });
    return res.status(200).json({ message: genericMessage });
  } catch (error) {
    if (error.name === "ZodError")
      return res.status(400).json({ message: "Enter a valid email address" });
    console.error("Password reset request failed:", error);
    return res.status(200).json({ message: genericMessage });
  }
};

export const resetPassword = async (req, res) => {
  try {
    const token = z.string().min(1).parse(req.query.token);
    const password = passwordSchema.parse(req.body.password);
    const user = await User.findOne({
      resetPasswordTokenHash: hashToken(token),
      resetPasswordTokenExpires: { $gt: new Date() },
    }).select("+password");
    if (!user)
      return res.status(400).json({ message: "Invalid or expired reset link" });

    user.password = password;
    user.resetPasswordTokenHash = undefined;
    user.resetPasswordTokenExpires = undefined;
    user.loginAttempts = 0;
    user.lockUntil = undefined;
    user.refreshTokenVersion += 1;
    await user.save();
    clearRefreshTokenCookie(res);
    return res
      .status(200)
      .json({ message: "Password reset successful. Please log in." });
  } catch (error) {
    if (error.name === "ZodError")
      return res.status(400).json({ message: validationMessage(error) });
    console.error("Password reset failed:", error);
    return res.status(500).json({ message: "Password reset failed" });
  }
};

export const refreshAccessToken = async (req, res) => {
  try {
    const token = req.cookies.refreshToken;
    if (!token) return res.status(401).json({ message: "Session expired" });
    const decoded = jwt.verify(token, process.env.JWT_REFRESH_SECRET);
    if (decoded.type !== "refresh") throw new Error("Wrong token type");
    const user = await User.findById(decoded.id);
    if (
      !user ||
      !user.isVerified ||
      decoded.version !== user.refreshTokenVersion
    )
      throw new Error("User unavailable");
    user.refreshTokenVersion += 1;
    await user.save();
    sendRefreshTokenCookie(
      res,
      generateRefreshToken(user._id, user.refreshTokenVersion),
    );
    return res
      .status(200)
      .json({
        accessToken: generateAccessToken(user._id),
        user: publicUser(user),
      });
  } catch {
    clearRefreshTokenCookie(res);
    return res.status(401).json({ message: "Session expired" });
  }
};

export const getCurrentUser = async (req, res) => {
  const user = await User.findById(req.userId);
  if (!user) return res.status(404).json({ message: "User not found" });
  return res.status(200).json({ user: publicUser(user) });
};

export const logout = async (req, res) => {
  try {
    const token = req.cookies.refreshToken;
    if (token) {
      const decoded = jwt.verify(token, process.env.JWT_REFRESH_SECRET);
      const user = await User.findById(decoded.id);
      if (user && decoded.version === user.refreshTokenVersion) {
        user.refreshTokenVersion += 1;
        await user.save();
      }
    }
  } catch {
    // Logout remains idempotent even when the cookie is invalid or expired.
  }
  clearRefreshTokenCookie(res);
  return res.status(200).json({ message: "Logged out successfully" });
};
