import "dotenv/config";
import express from "express";
import cookieParser from "cookie-parser";
import cors from "cors";
import helmet from "helmet";
import connectDB from "./config/db.js";
import authRoutes from "./routes/authRoutes.js";

const requiredEnv = [
  "MONGO_URI",
  "JWT_ACCESS_SECRET",
  "JWT_REFRESH_SECRET",
  "GMAIL_USER",
  "GMAIL_APP_PASSWORD",
  "EMAIL_FROM",
  "CLIENT_URL",
];
const missingEnv = requiredEnv.filter(
  (key) => !process.env[key] || process.env[key].startsWith("replace-"),
);
const shortSecrets = ["JWT_ACCESS_SECRET", "JWT_REFRESH_SECRET"].filter(
  (key) => (process.env[key] || "").length < 32,
);
if (missingEnv.length || shortSecrets.length) {
  const problems = [
    ...(missingEnv.length ? [`missing values: ${missingEnv.join(", ")}`] : []),
    ...(shortSecrets.length
      ? [
          `JWT secrets must be at least 32 characters: ${shortSecrets.join(", ")}`,
        ]
      : []),
  ];
  throw new Error(`Invalid environment configuration (${problems.join("; ")})`);
}

connectDB();

const app = express();

app.use(helmet());

app.use(
  cors({
    origin: process.env.CLIENT_URL,
    credentials: true,
  }),
);

app.use(express.json());
app.use(cookieParser());

app.use("/api/auth", authRoutes);

app.get("/", (req, res) => {
  res.json({ status: "Server is running" });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
