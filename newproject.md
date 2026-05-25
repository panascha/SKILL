# [PROJECT_NAME] 🚀

> [สรุปสั้นๆ 1-2 ประโยค: โปรเจกต์นี้คืออะไร แก้ปัญหาอะไร สำหรับใคร]
>
> **ตัวอย่าง:** ระบบจัดการชั่วโมงสะสมนักศึกษา KKU ที่ให้นักศึกษาลงทะเบียนกิจกรรมออนไลน์ และ Admin ดูรายงานแบบ Real-time ได้ทันที

---

## 🌟 Features

<!-- ✏️ แก้ไขตามฟีเจอร์จริงของโปรเจกต์ -->

- 🔐 **Firebase Auth** — ล็อกอินด้วย Google Account จำกัดเฉพาะ `@domain.com`
- 📋 **Google Sheets Backend** — บันทึกข้อมูล Static ปริมาณมาก เปิดดูได้ง่ายผ่าน Sheets
- 🔄 **Firebase Realtime DB** — *(ถ้าใช้)* ซิงค์ข้อมูล Live เช่น สถานะ, คะแนน, การแจ้งเตือน
- 🐘 **Supabase** — *(ถ้าใช้)* Relational DB (PostgreSQL), Auth, Realtime, Storage ในที่เดียว
- 📱 **Responsive UI** — รองรับทั้ง Mobile และ Desktop ด้วย Tailwind CSS
- 🛠️ **Admin Dashboard** — หน้าหลังบ้านสำหรับจัดการข้อมูลและดูรีพอร์ต

---

## 🛠️ Tech Stack

| Layer | Technology | หน้าที่ |
|---|---|---|
| **Frontend** | HTML5 / Vanilla JS (ES Modules) | UI และ Logic หน้าบ้าน |
| **Styling** | Tailwind CSS via Vite | Responsive Design |
| **Build Tool** | Vite | Bundler, Dev Server, Multi-page |
| **Auth** | Firebase Authentication | Google Sign-In, Session |
| **Auth (alt)** | Supabase Auth *(optional)* | Email/OAuth Sign-In แทน Firebase Auth |
| **DB (Static)** | Google Apps Script + Sheets | เก็บข้อมูลปริมาณมาก, Reports |
| **DB (Realtime)** | Firebase Realtime DB *(optional)* | Live Sync, Presence, Notify |
| **DB (Relational)** | Supabase (PostgreSQL) *(optional)* | ข้อมูลที่ต้องการ Relation, Foreign Key, Join |
| **Storage** | Supabase Storage *(optional)* | อัปโหลดไฟล์/รูป แทน Firebase Storage |
| **Hosting** | GitHub Pages / Vercel | Deploy Static Web |

> 💡 **เลือก DB ตามความต้องการ:**
> - ข้อมูลเยอะ ไม่มี Relation → **Google Sheets + GAS**
> - ต้องการ Live Sync / Presence → **Firebase RTDB**
> - มี Relation, Foreign Key, JOIN → **Supabase (PostgreSQL)**

---

## 📂 Project Structure

```text
[project-root]/
├── public/                         # Static assets (favicon, manifest.json)
├── src/
│   ├── assets/                     # รูปภาพ, โลโก้, ฟอนต์ (ให้ Vite จัดการ)
│   ├── components/                 # UI Components ที่ใช้ซ้ำข้ามหน้า
│   │   ├── Navbar.js
│   │   ├── Sidebar.js              # (ถ้ามี)
│   │   └── Modal.js
│   ├── pages/                      # แต่ละหน้า (เก็บ HTML + JS คู่กัน)
│   │   ├── admin/
│   │   │   ├── admin.html
│   │   │   └── admin.js
│   │   └── [page-name]/
│   │       ├── [page-name].html
│   │       └── [page-name].js
│   ├── services/                   # ติดต่อ Backend เท่านั้น (ห้ามยุ่ง DOM)
│   │   ├── firebase.js             # Firebase SDK init (Auth + RTDB)
│   │   ├── auth.service.js         # Login, Logout, onAuthStateChanged
│   │   ├── db.service.js           # Firebase RTDB read/write (ถ้าใช้)
│   │   ├── gas.service.js          # fetch() ไป GAS Web App URL
│   │   └── supabase.service.js     # Supabase client + query helpers (ถ้าใช้)
│   ├── styles/
│   │   └── global.css              # @tailwind directives + Global CSS
│   ├── utils/
│   │   └── helpers.js              # formatDate(), localStorage wrapper, ฯลฯ
│   └── main.js                     # Auth Guard ระดับ App (redirect ถ้ายังไม่ login)
├── google-apps-script/             # GAS Source (Version Control)
│   ├── Code.js                     # doGet(), doPost(), Sheet logic
│   └── appsscript.json
├── supabase/                       # Supabase migrations & seed (ถ้าใช้)
│   ├── migrations/
│   │   └── 0001_init.sql           # CREATE TABLE, RLS policies
│   └── seed.sql                    # ข้อมูลตัวอย่างสำหรับ dev
├── index.html                      # Entry Point / Landing + Login Page
├── .env                            # ❌ ห้าม commit (อยู่ใน .gitignore)
├── .env.example                    # ✅ Template ตัวแปรที่ต้องกรอก
├── .gitignore
├── package.json
├── tailwind.config.js
└── vite.config.js                  # Multi-page input config
```

---

## ⚙️ Config Files

### `vite.config.js`
```js
import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  base: './',   // สำคัญ: ทำให้ path ไม่เพี้ยนบน GitHub Pages / Vercel
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main:  resolve(__dirname, 'index.html'),
        // ✏️ เพิ่ม/ลบ หน้าตามโปรเจกต์
        home:  resolve(__dirname, 'src/pages/home/home.html'),
        admin: resolve(__dirname, 'src/pages/admin/admin.html'),
      },
    },
  },
});
```

### `.env.example`
```env
# Firebase
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_DATABASE_URL=        # (ถ้าใช้ Realtime DB)
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=

# Google Apps Script
VITE_GAS_WEBAPP_URL=https://script.google.com/macros/s/.../exec

# Auth (Domain Whitelist)
VITE_ALLOWED_EMAIL_DOMAIN=@domain.com

# Supabase (ถ้าใช้ Relational DB)
VITE_SUPABASE_URL=https://[project-ref].supabase.co
VITE_SUPABASE_ANON_KEY=
```

### `tailwind.config.js`
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{html,js}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

---

## 🗄️ Database Schema

> ⚠️ ทั้ง Firebase RTDB, Google Sheets และ Supabase เป็น Schemaless หรือ Flexible —
> **ต้องล็อกชื่อ field / column ไว้ที่นี่** เพื่อป้องกัน `userId` ปนกับ `user_id`

---

### 📊 Google Sheets Tables

#### Table: `[table_name]` (Sheet ชื่อ: `[Sheet Tab Name]`)
| Column | Type | Required | Description | Example |
|---|---|---|---|---|
| `user_id` | String | ✅ | Firebase Auth UID | `abc123xyz` |
| `email` | String | ✅ | อีเมลผู้ใช้ | `test@domain.com` |
| `created_at` | ISOString | ✅ | เวลาบันทึก (UTC) | `2026-05-21T22:00:00Z` |
| `[field]` | String/Number/Boolean | | [คำอธิบาย] | |

<!-- ✏️ เพิ่ม Table ตามที่ใช้งานจริง -->

---

### 🔥 Firebase Realtime DB Structure

> ใช้เฉพาะเมื่อโปรเจกต์ต้องการ **Real-time sync** เช่น presence, live score, notification

```json
{
  "presence": {
    "$user_id": {
      "is_online": true,
      "last_seen": 1779382583
    }
  }
}
```
<!-- ✏️ แก้ไข JSON structure ตามที่ใช้งานจริง หรือลบ section นี้ถ้าไม่ใช้ RTDB -->

---

### 🐘 Supabase (PostgreSQL) Schema

> ใช้เมื่อโปรเจกต์ต้องการ **Relational data** เช่น foreign key, JOIN, aggregate query
> หรือต้องการ **Row Level Security (RLS)** ระดับ database

#### เมื่อไหรควรใช้ Supabase แทน Sheets/RTDB

| เงื่อนไข | แนะนำ |
|---|---|
| ข้อมูลมี relation ซับซ้อน (1-to-many, many-to-many) | ✅ Supabase |
| ต้องการ filter/sort/paginate ฝั่ง server | ✅ Supabase |
| ต้องการ Row-Level Security ต่อ user | ✅ Supabase |
| ข้อมูล append-only เยอะ ไม่ต้อง query ซับซ้อน | ✅ Google Sheets |
| ต้องการ Realtime presence / live counter | ✅ Firebase RTDB |

#### ตัวอย่าง Table Definitions

```sql
-- supabase/migrations/0001_init.sql

-- ตาราง Users (ขยายจาก Supabase Auth)
create table public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  display_name text,
  role        text not null default 'user',  -- 'user' | 'admin'
  created_at  timestamptz not null default now()
);

-- ✏️ เพิ่ม Table ตามโปรเจกต์ เช่น:
-- create table public.[table_name] (
--   id         uuid primary key default gen_random_uuid(),
--   user_id    uuid not null references public.profiles(id),
--   [field]    text,
--   created_at timestamptz not null default now()
-- );
```

#### Row Level Security (RLS) — บังคับเปิดทุก Table

```sql
-- ตัวอย่าง RLS สำหรับตาราง profiles
alter table public.profiles enable row level security;

-- อ่านได้เฉพาะ record ของตัวเอง
create policy "Users can read own profile"
  on public.profiles for select
  using (auth.uid() = id);

-- Admin อ่านได้ทุก record
create policy "Admins can read all profiles"
  on public.profiles for select
  using (
    exists (
      select 1 from public.profiles
      where id = auth.uid() and role = 'admin'
    )
  );

-- ✏️ เพิ่ม policy สำหรับแต่ละ table และ operation (insert, update, delete)
```

#### Supabase Service (`src/services/supabase.service.js`)

```js
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

// ─── ตัวอย่าง helper functions ───────────────────────────────────────────────

/** ดึง profile ของ user ที่ login อยู่ */
export async function getMyProfile() {
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .single();
  if (error) throw error;
  return data;
}

/** ดึงข้อมูลแบบมี relation (ตัวอย่าง) */
export async function getItemsWithOwner() {
  const { data, error } = await supabase
    .from('[table_name]')
    .select(`*, profiles(display_name, email)`)
    .order('created_at', { ascending: false });
  if (error) throw error;
  return data;
}

/** Insert row */
export async function createItem(payload) {
  const { data, error } = await supabase
    .from('[table_name]')
    .insert(payload)
    .select()
    .single();
  if (error) throw error;
  return data;
}

export { supabase };
```

#### ER Diagram (อัปเดตตามโปรเจกต์)

```
auth.users (Supabase built-in)
    │ 1
    │
    ▼ *
public.profiles ──────────── public.[table_name]
  id (PK)                       id (PK)
  email                         user_id (FK → profiles.id)
  display_name                  [field]
  role                          created_at
  created_at
```

<!-- ✏️ วาด ER Diagram ให้ตรงกับ table จริง -->

---

### 🔗 GAS API Payload Spec

#### `POST /exec` — บันทึกข้อมูล
```json
{
  "action": "[actionName]",
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

#### `GET /exec?action=[actionName]&param=value` — ดึงข้อมูล
```json
{
  "status": "success",
  "data": [ { "field1": "value1" } ]
}
```

<!-- ✏️ เพิ่ม action ทั้งหมดที่ GAS รองรับ -->

---

## 🛡️ Contributing Guidelines

### Separation of Concerns (กฎเหล็ก)

| Layer | อนุญาต | ห้ามเด็ดขาด |
|---|---|---|
| `src/pages/` | import service → แสดงผล DOM | เขียน `fetch()` หรือ Firebase/Supabase logic ตรงๆ |
| `src/services/` | เชื่อม API, return data | `document.getElementById()`, จัดการ DOM |
| `src/components/` | สร้าง/อัปเดต DOM ภายในตัวเอง | เรียก API ตรงๆ |

### Code Style
- ✅ ใช้ ES Modules (`import/export`) เสมอ
- ✅ ใช้ Tailwind utility classes ใน HTML
- ❌ ห้ามใช้ inline style `style="..."`
- ❌ ห้ามเขียนฟังก์ชันลอยๆ ใน global scope

### Git Workflow
- ❌ ห้าม push ตรงเข้า `main`
- ✅ แตก branch ทุกครั้ง: `feature/[name]`, `fix/[name]`, `chore/[name]`
- ✅ ตั้งชื่อ commit ให้อ่านเข้าใจ: `feat: add login page`, `fix: gas timeout`

### AI / Vibe Coding Rules
- ✅ AI ต้องยึดโครงสร้าง `services/` ← → `pages/` เสมอ
- ✅ ชื่อ field / column ทุกตัวต้องตรงกับ DATABASE SCHEMA ด้านบน
- ✅ Supabase query ต้องอยู่ใน `supabase.service.js` เท่านั้น ห้ามเรียก `supabase` ตรงจากหน้า
- ❌ ห้าม AI สร้างไฟล์นอกโครงสร้างที่กำหนดโดยไม่ได้รับอนุมัติ
- ❌ ห้าม AI เพิ่ม column ใน Supabase โดยไม่อัปเดต migration และ schema ใน README นี้

---

## ⚡ Getting Started

### Prerequisites
- Node.js v18+
- Firebase Project (พร้อม Web App credentials)
- Google Sheet + GAS deployment URL *(ถ้าใช้ GAS)*
- Supabase Project *(ถ้าใช้ Relational DB)* — สร้างได้ที่ [supabase.com](https://supabase.com)

### Installation
```bash
git clone <REPOSITORY_URL>
cd <PROJECT_FOLDER>
npm install
```

### Environment Variables
```bash
cp .env.example .env
# กรอกค่าทั้งหมดใน .env
```

### Development
```bash
npm run dev
# เปิดที่ http://localhost:5173
```

---

## 📦 Build & Deployment

### Build
```bash
npm run build
# output → /dist
```

### Option A: Vercel *(แนะนำ)*
1. เชื่อม GitHub Repo กับ Vercel Dashboard
2. ตั้งค่า: Framework = `Vite`, Build Command = `npm run build`, Output = `dist`
3. เพิ่ม Environment Variables ใน Vercel Settings
4. Deploy

### Option B: GitHub Pages
1. ตั้ง `base: './'` ใน `vite.config.js` *(ทำแล้ว)*
2. ใช้ GitHub Actions หรือ push `/dist` ไปที่ branch `gh-pages`

---

## 🔧 Google Apps Script Setup

1. เปิด Google Sheet → Extensions → Apps Script
2. วางโค้ดจาก `google-apps-script/Code.js`
3. Deploy → New Deployment → Web App
   - Execute as: **Me**
   - Who has access: **Anyone**
4. คัดลอก Web App URL → ใส่ใน `.env` ที่ `VITE_GAS_WEBAPP_URL`

---

## 🐘 Supabase Setup

> ข้ามขั้นตอนนี้ถ้าโปรเจกต์ไม่ได้ใช้ Supabase

1. สร้าง Project ใหม่ที่ [supabase.com/dashboard](https://supabase.com/dashboard)
2. ไปที่ **Settings → API** → คัดลอก `Project URL` และ `anon public` key → ใส่ใน `.env`
3. รัน migration เพื่อสร้าง table:
   ```bash
   # วิธีที่ 1: ผ่าน Supabase CLI (แนะนำ)
   npx supabase db push

   # วิธีที่ 2: Copy-paste SQL ใน Supabase Dashboard → SQL Editor
   # เปิดไฟล์ supabase/migrations/0001_init.sql แล้ว run
   ```
4. ติดตั้ง Supabase JS client:
   ```bash
   npm install @supabase/supabase-js
   ```
5. ตรวจสอบว่า **Row Level Security (RLS)** เปิดอยู่ทุก table ก่อน go live

---

## 🗂️ .gitignore Checklist

```text
node_modules/
dist/
.env
.env.local
.env.*.local
.DS_Store
Thumbs.db
*.log
.vscode/
.idea/
.supabase/
```

---

## 📝 License & Credits

[MIT / Private] — © 2026 [ชื่อทีม/ผู้พัฒนา]