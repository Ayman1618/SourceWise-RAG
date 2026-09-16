"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AuthCard } from "@/components/AuthCard";
import { ArrowRight, Lock, Mail, User, Building, CheckCircle2 } from "lucide-react";

export default function SignUpPage() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    department: "Engineering",
    password: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <AuthCard
        title="Account Requested"
        subtitle="Verification link sent to your work email"
      >
        <div className="py-6 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto border border-emerald-200">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <p className="text-sm text-slate-700">
            Thank you, <span className="font-semibold text-slate-900">{formData.name || "User"}</span>. An enterprise access request has been logged for <span className="font-medium text-slate-900">{formData.email}</span>.
          </p>
          <div className="pt-4">
            <Link
              href="/login"
              className="inline-flex justify-center items-center space-x-2 w-full py-2.5 px-4 rounded-md text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 transition-colors"
            >
              <span>Proceed to Sign In</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Create your account"
      subtitle="Get started with SourceWise RAG enterprise knowledge assistant"
    >
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="full-name" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Full Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <User className="w-4 h-4" />
            </div>
            <input
              id="full-name"
              name="name"
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Om Bankar"
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
          </div>
        </div>

        <div>
          <label htmlFor="work-email" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Work Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              id="work-email"
              name="email"
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="name@company.com"
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
          </div>
        </div>

        <div>
          <label htmlFor="department" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Department / Organization
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Building className="w-4 h-4" />
            </div>
            <select
              id="department"
              name="department"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 bg-white"
            >
              <option value="Engineering">Engineering & Development</option>
              <option value="Product">Product Management</option>
              <option value="Legal">Legal & Compliance</option>
              <option value="Operations">Operations & Knowledge</option>
              <option value="Research">Research & Analytics</option>
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="password" className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="••••••••"
              className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
            />
          </div>
        </div>

        <button
          type="submit"
          className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-900 hover:bg-brand-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors mt-2"
        >
          <span>Create Account</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <div className="text-center pt-2">
          <p className="text-xs text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-slate-900 hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </form>
    </AuthCard>
  );
}
