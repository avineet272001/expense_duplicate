# Expense Management — Combined Project

Both modules now live in **one** FastAPI app and share the same database
models, so there's a single server to run and a single source of truth for
expenses.

```
expense-management/
├── app/
│   ├── main.py              ← combined app: mounts both routers + both frontends
│   ├── config.py / database.py
│   ├── models.py            ← unified SQLAlchemy models
│   ├── schemas.py           ← unified Pydantic schemas (incl. admin ones)
│   ├── crud.py               ← unified data-access layer
│   └── routes/
│       ├── expense.py       ← employee: create / list / view / edit / delete
│       ├── dashboard.py      ← employee dashboard summary
│       ├── reports.py        ← category spend report
│       └── admin.py          ← admin: approve / reject / mark-paid + queues
├── frontend/                 ← Employee UI  → served at  /
├── admin-frontend/           ← Admin UI     → served at  /admin-ui/
├── sql/                       ← reference schema
├── requirements.txt
└── .env
```

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

- Employee workspace: **http://localhost:8080/**
- Admin panel: **http://localhost:8080/admin-ui/**
- API docs: **http://localhost:8080/docs**

## How the two modules split responsibility

**Employee module** (`/expenses`, `/dashboard`, `/reports`)
- Submit a new expense (with an optional receipt upload)
- Browse/search/filter their own expenses and see live status
- View a receipt, or delete an expense while it's still `Pending`
- A "Admin panel" link in the sidebar jumps straight to `/admin-ui/`

**Admin module** (`/admin/*`)
- Dashboard with totals + pending/approved/rejected/paid counts
- A **Pending approvals** queue — Approve or Reject (with a reason) each claim
- An **Approved** queue — Mark paid once a payout has gone out
- **Paid** and **Rejected** history views, plus the same category report
- A "← Employee workspace" link back to `/`

Both UIs share the same design system (`Ledger`) so they feel like one
product — the admin panel just uses a slate accent instead of teal to make
it visually distinct as the "admin" surface.

## What changed from the two separate modules

- The old `Admin-Module/` folder (its own FastAPI app, its own copy of the
  models/db config, running on a separate port) was folded into `app/` —
  there is now one `models.py`/`schemas.py`/`crud.py`, so employee-side and
  admin-side data are always in sync.
- Approve / reject / mark-paid actions were removed from the employee UI
  (an employee shouldn't be able to approve their own expense) and now
  live only in the admin panel.
- Added guards so an expense can only be approved/rejected while `Pending`,
  and only marked paid while `Approved` — matches the status lifecycle
  already encoded in `sql/02_tables.sql`.
- Fixed a latent bug where two expenses created within the same second
  could collide on `expense_number` (it was built from a whole-second
  timestamp); a short random suffix was added.
