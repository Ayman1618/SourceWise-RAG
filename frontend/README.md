# SourceWise RAG — Frontend Foundation

This directory contains the Next.js frontend application foundation for **SourceWise RAG**, an enterprise knowledge assistant built for trustworthy, evidence-first document retrieval, grounding, and verification.

## Purpose

The frontend foundation provides a clean, robust, and responsive application shell and landing page establishing the visual identity and core product commitment of SourceWise RAG: **Retrieve. Ground. Verify.**

This PR (PR 3) focuses strictly on setting up the initial application shell and technical layout so that subsequent feature PRs (e.g., query interface, citation rendering, retrieval inspector) can build upon a stable architecture.

## Technologies Used

- **Framework**: [Next.js](https://nextjs.org/) (v14.2+, App Router)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Icons**: [Lucide React](https://lucide.react.dev/)
- **Linting & Code Quality**: [ESLint](https://eslint.org/) (`eslint-config-next`)
- **Package Manager**: `npm`

## Installation

Ensure Node.js (v18.x or v20.x+) is installed in your development environment.

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies using npm
npm install
```

## Running the Development Server

To start the local development server:

```bash
npm run dev
```

The application will be available at the expected local URL:
**[http://localhost:3000](http://localhost:3000)**

## Linting

To run the ESLint code quality checks:

```bash
npm run lint
```

To run a production build verification:

```bash
npm run build
```

## Application Structure

```
frontend/
├── app/
│   ├── globals.css      # Base Tailwind CSS directives and global theme styles
│   ├── layout.tsx       # Root layout shell (Header, Main, Footer)
│   └── page.tsx         # Foundation landing page
├── components/
│   ├── EvidenceBadge.tsx # "Retrieve. Ground. Verify." visual badge
│   ├── Footer.tsx        # Standard footer component
│   └── Header.tsx        # Enterprise header navigation shell
├── lib/
│   └── utils.ts          # Utility functions for class merging (cn helper)
├── public/              # Static assets
├── .eslintrc.json       # ESLint configuration
├── next.config.mjs      # Next.js configuration
├── package.json         # Dependencies and scripts
├── postcss.config.js    # PostCSS configuration
├── tailwind.config.ts   # Tailwind CSS configuration with brand colors
└── tsconfig.json        # TypeScript compiler configuration
```

## Current Implementation Limitations

- **No Active RAG API Calls**: This foundation PR does not make API calls to the backend service.
- **No Mock Responses / Fake Sources**: In accordance with project guidelines, no mock AI outputs or synthetic citations are rendered.
- **Placeholder Actions**: The "Ask a Question" and "Knowledge Base" buttons serve as visual entry points and do not yet execute navigation or state transitions.
- **No Authentication or State Management**: Backend integration, auth providers, and complex global state management will be introduced in subsequent PRs.
