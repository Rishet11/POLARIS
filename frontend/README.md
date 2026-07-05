# POLARIS frontend

Dashboard UI for the POLARIS factoring back office demo: cash application (payment matching), collections, and portfolio monitoring.

## Stack

- Next.js 16 (App Router)
- Tailwind CSS 4
- shadcn/ui components

## Running

The dashboard reads all data from the FastAPI backend and does not run standalone. Start the API first (see `../DEMO.md`), then:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Configuration

Set `NEXT_PUBLIC_API_URL` to point at the backend if it's not on the default `http://localhost:8600`.
