# EventPhotoUploader – Site Journey & Flow

## 1. Authentication
### Sign-Up
- GET  `/auth/sign-up` → `sign_up.html`  
- POST `/auth/sign-up`  
  • Creates user, sends verification email  
  • Redirect → `/pricing`

### Verify Email
- GET `/auth/verify-email?token=…` → `thank_you_verification.html`

### Log-In
- GET  `/auth/login` → `login.html`  
- POST `/auth/login`  
  • Validates credentials → issues JWT cookie  
  • Redirect → `/auth/profile`

### Log-Out
- GET `/auth/logout`  
  • Deletes session cookie  
  • Redirect → `/auth/login`

## 2. Profile Dashboard
- GET `/auth/profile` → `profile.html`  
  • Shows user info, plan details  
  • Lists “Your Events”  
  • Actions:  
    – Create new event (if under limit) → `/auth/events/create`  
    – Delete account → `/auth/delete-account`

## 3. Account Deletion
- GET  `/auth/delete-account` → `delete_account.html`  
- POST `/auth/delete-account`  
  • Cascade-deletes sessions, events, user  
  • Clears cookie → Redirect `/`

## 4. Event Management  
```mermaid
flowchart TD
  A[Profile] -->|Create New Event| B[GET /auth/events/create]
  B --> C[create_event.html]
  C -->|submit| D[POST /auth/events]
  D --> E[event_created.html]
  A -->|View| F[GET /auth/events/{id}] 
  F --> G[event.html]
  A -->|QR| H[GET /auth/event-qr] 
```

### Create Event
- GET  `/auth/events/create` → `create_event.html` (fills “type” dropdown from DB)  
- POST `/auth/events`  
  • Generates `event_code` & `event_password`  
  • Persists new `Event` and its `storage_path`  
  • Renders `event_created.html` with codes  

### View Single Event  
- GET `/auth/events/{event_id}` → `event.html`  
  • Shows details + links:  
    – Upload (`/upload/{code}/{password}`)  
    – Gallery (`/api/gallery/{id}`)

### List All Events  
- GET `/auth/events` → `events.html`

## 5. Photo Upload & Gallery
- **Upload**: mounted at `/upload/{code}/{password}` (upload_router)  
- **Gallery**: `/api/gallery/{event_id}` → `gallery.html`

---

Keep this file up-to-date as you add routes, change templates or business logic. Whenever you ask Copilot questions (“how does the pricing limit work?” or “show me the upload flow”) it can refer back to this doc as your source-of-truth.# filepath: docs/site_journey.md

# EventPhotoUploader – Site Journey & Flow

## 1. Authentication
### Sign-Up
- GET  `/auth/sign-up` → `sign_up.html`  
- POST `/auth/sign-up`  
  • Creates user, sends verification email  
  • Redirect → `/pricing`

### Verify Email
- GET `/auth/verify-email?token=…` → `thank_you_verification.html`

### Log-In
- GET  `/auth/login` → `login.html`  
- POST `/auth/login`  
  • Validates credentials → issues JWT cookie  
  • Redirect → `/auth/profile`

### Log-Out
- GET `/auth/logout`  
  • Deletes session cookie  
  • Redirect → `/auth/login`

## 2. Profile Dashboard
- GET `/auth/profile` → `profile.html`  
  • Shows user info, plan details  
  • Lists “Your Events”  
  • Actions:  
    – Create new event (if under limit) → `/auth/events/create`  
    – Delete account → `/auth/delete-account`

## 3. Account Deletion
- GET  `/auth/delete-account` → `delete_account.html`  
- POST `/auth/delete-account`  
  • Cascade-deletes sessions, events, user  
  • Clears cookie → Redirect `/`

## 4. Event Management  
```mermaid
flowchart TD
  A[Profile] -->|Create New Event| B[GET /auth/events/create]
  B --> C[create_event.html]
  C -->|submit| D[POST /auth/events]
  D --> E[event_created.html]
  A -->|View| F[GET /auth/events/{id}] 
  F --> G[event.html]
  A -->|QR| H[GET /auth/event-qr] 
```

### Create Event
- GET  `/auth/events/create` → `create_event.html` (fills “type” dropdown from DB)  
- POST `/auth/events`  
  • Generates `event_code` & `event_password`  
  • Persists new `Event` and its `storage_path`  
  • Renders `event_created.html` with codes  

### View Single Event  
- GET `/auth/events/{event_id}` → `event.html`  
  • Shows details + links:  
    – Upload (`/upload/{code}/{password}`)  
    – Gallery (`/api/gallery/{id}`)

### List All Events  
- GET `/auth/events` → `events.html`

## 5. Photo Upload & Gallery
- **Upload**: mounted at `/upload/{code}/{password}` (upload_router)  
- **Gallery**: `/api/gallery/{event_id}` → `gallery.html`

---

Keep this file up-to-date as you add routes, change templates or business logic. Whenever you ask Copilot questions (“how does the pricing limit work?” or “show me the upload flow”) it can refer back to this doc as your source-of-truth.