import express from "express";
import {
    register,
    verifyEmail,
    login,
    forgotPassword,
    resetPassword,
    resendVerification,
    refreshAccessToken,
    getCurrentUser,
    logout,
} from "../controllers/authController.js";
import { protect } from "../middleware/authMiddleware.js";
import { authLimiter, forgotPasswordLimiter } from "../middleware/rateLimiter.js";

const router = express.Router();

router.post("/register", authLimiter, register);
router.get("/verify-email", verifyEmail);
router.post("/resend-verification", authLimiter, resendVerification);
router.post("/login", authLimiter, login);
router.post("/forgot-password", forgotPasswordLimiter, forgotPassword);
router.post("/reset-password", resetPassword);
router.post("/refresh", refreshAccessToken);
router.get("/me", protect, getCurrentUser);
router.post("/logout", logout);

export default router;