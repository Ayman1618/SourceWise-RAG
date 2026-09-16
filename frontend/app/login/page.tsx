"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AuthCard } from "@/components/AuthCard";
import { ArrowRight, Lock, Mail, CheckCircle2 } from "lucide-react";

export default function LoginPage() {
  const [signedIn, setSignedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSignedIn(true);
  };

  if (signedIn) {
    return (
      <AuthCard
        title="Welcome Back"
        subtitle="SourceWise RAG Knowledge Portal"
      >
        <div className="py-6 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <p className="text-sm text-slate-700">
            Authenticated as <span className="font-semibold text-slate-900">{email || "enterprise.user@company.com"}</span>.
          </p>
          <div className="pt-4">
            <Link
              href="/"
              className="inline-flex justify-center items-center space-x-2 w-full py-2.5 px-4 rounded-md text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 transition-colors"
            >
              <span>Go to Knowledge Home</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Sign in to your account"
      subtitle="Access grounded enterprise documentation and citations"
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Work Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="password" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Password
            </label>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-900 hover:bg-brand-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors mt-2"
        >
          <span>Sign In</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <div className="text-center pt-2">
          <p className="text-xs text-slate-600">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-semibold text-slate-900 hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </form>
    </AuthCard>
  );
}
