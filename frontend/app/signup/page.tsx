"use client";

import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowRight, Lock, Mail, User, Building } from "lucide-react";

export default function SignUpPage() {
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg border border-slate-200 shadow-sm">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex w-12 h-12 rounded bg-brand-900 items-center justify-center text-white shadow-sm mb-4">
            <ShieldCheck className="w-6 h-6 text-slate-100" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Create your account
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            Get started with SourceWise RAG enterprise knowledge assistant
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-5" onSubmit={(e) => e.preventDefault()}>
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
              <input
                id="department"
                name="department"
                type="text"
                placeholder="Engineering / Product"
                className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
              />
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
                placeholder="••••••••"
                className="block w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-brand-900 hover:bg-brand-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors"
          >
            <span>Create Account</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Notice & Footer links */}
        <div className="pt-4 border-t border-slate-100 text-center space-y-3">
          <p className="text-xs text-slate-500">
            Access to SourceWise RAG is governed by internal enterprise document access policies.
          </p>
          <div className="text-xs">
            <Link href="/" className="font-medium text-slate-700 hover:text-slate-900 underline">
              ← Return to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
