# SafeAlert - Project Todos & Roadmap

**Last Updated:** 20 Mei 2026  
**Total Todos:** 60  
**Status:** Planning Phase → Development Phase

---

## 📊 Quick Statistics

| Phase | Todos | Status |
|-------|-------|--------|
| Phase 2: Backend | 12 | ⏳ Pending |
| Phase 3: Mobile | 15 | ⏳ Pending |
| Phase 4: Dashboard | 12 | ⏳ Pending |
| Phase 5-7: Integration & Deploy | 11 | ⏳ Pending |
| Phase 8+: Future Enhancements | 10 | 💡 Planning |
| **TOTAL** | **60** | |

---

## 🔄 Phase 2: Backend Foundation (Dev 2)

**Goal:** API dasar siap di-test via Postman. All endpoints return correct responses with proper authentication.

### User Management
1. **backend-user-model** - Implement User Model & Serializers
   - Create User model with fields: name, phone, floor, disability_type, fcm_token, admin_status
   - Setup UserSerializer for registration endpoint
   - Add phone field validation (unique constraint)

2. **backend-auth-jwt** - Setup JWT Authentication
   - Implement Admin authentication using SimpleJWT
   - Create login endpoint `POST /api/auth/login/`
   - Return JWT token on successful login
   - Add token refresh mechanism

3. **backend-register-endpoint** - Create User Registration Endpoint
   - Implement `POST /api/auth/register/` endpoint
   - Accept user data and FCM token
   - Store in database with admin_status=pending
   - Return user_id and confirmation message

4. **backend-user-endpoints** - Implement User Management Endpoints
   - Create `GET /api/users/` to list all users (filtered by status)
   - Implement `PATCH /api/users/{id}/status/` to update user status
   - Add authorization checks (admin only)
   - Include pagination and filtering

### Alarm & Notification Management
5. **backend-alarm-model** - Implement Alarm_Log Model
   - Create AlarmLog model with fields: message, triggered_by (FK Admin), triggered_at, total_recipients, status
   - Add status enum: active/cancelled
   - Setup proper timestamps

6. **backend-fcm-service** - Setup FCM Integration Service
   - Install & configure firebase-admin-python
   - Create fcm_service.py module
   - Implement multicast notification sending
   - Handle token errors gracefully
   - Add logging for debugging

7. **backend-alarm-trigger** - Implement Alarm Trigger Endpoint
   - Create `POST /api/alarms/trigger/` endpoint
   - Query all users with admin_status IN (safe, evacuating, trapped)
   - Fetch FCM tokens for each user
   - Send multicast notification via FCM service
   - Update total_recipients in Alarm_Log
   - Return alarm_id and status

8. **backend-alarm-history** - Implement Alarm History Endpoint
   - Create `GET /api/alarms/` to list all alarms with pagination
   - Include confirmation count per alarm
   - Implement `GET /api/alarms/{id}/confirmations/` for detail view
   - Show list of users with confirmation status

9. **backend-cancel-alarm** - Implement Alarm Cancel Endpoint
   - Create `POST /api/alarms/{id}/cancel/` endpoint
   - Send cancel FCM payload to all users
   - Update alarm status to cancelled
   - Return confirmation message

### Confirmation & Tracking
10. **backend-confirmation-model** - Implement Confirmation Model
    - Create Confirmation model with fields: user_id, alarm_id, user_reported_status, confirmed_at
    - Setup foreign keys to User and Alarm_Log
    - Add status enum: safe/trapped/evacuating

11. **backend-confirm-endpoint** - Implement Confirmation Endpoint
    - Create `POST /api/confirm/` endpoint
    - Accept alarm_id, user_id, user_reported_status
    - Store confirmation in database
    - Return confirmation record with timestamp

### Testing & Validation
12. **backend-testing** - Test All API Endpoints
    - Create comprehensive test suite using pytest or Postman
    - Test all endpoints: register, login, user list, alarm trigger, confirm, cancel
    - Verify JWT token authentication
    - Test error scenarios (invalid phone, missing fields)
    - Performance test with 1000+ mock users

---

## 📱 Phase 3: Mobile Development (Dev 1)

**Goal:** App bisa registrasi → terima notifikasi → multisensory alert → konfirmasi → emergency calls

### UI Screens
1. **mobile-registration-ui** - Build Registration Screen UI
   - Create form with inputs: name, phone, floor (number picker), disability_type (radio)
   - Add form validation (phone format, floor range)
   - Implement Daftar button with loading state
   - Show success/error messages

2. **mobile-home-screen** - Build Home/Standby Screen
   - Create simple home screen: "SafeAlert Aktif"
   - Display user info: name, floor, verification status
   - Add 2 big red emergency buttons: Hubungi 113, Hubungi 110
   - Setup navigation to other screens

3. **mobile-alarm-screen** - Build Fullscreen Alarm Screen
   - Create fullscreen alert UI with red background
   - Display alarm message in white text (32sp+)
   - Add 3 confirmation buttons: [SAYA AMAN] [SAYA TERJEBAK] [SEDANG EVAKUASI]
   - Setup screen to wake device and force to foreground

4. **mobile-cancel-screen** - Build Cancel/All-Clear Screen
   - Create green screen with "AMAN. KEMBALI BEKERJA." message
   - Setup auto-dismiss after 5 seconds
   - Stop all vibration/flash/sound immediately

### Firebase & Notifications
5. **mobile-firebase-setup** - Setup Firebase Messaging
   - Initialize Firebase SDK in Flutter
   - Generate and retrieve FCM token
   - Save token to SharedPreferences after registration
   - Handle token refresh

6. **mobile-background-handler** - Implement FCM Background Handler
   - Setup firebase_messaging background handler
   - Parse incoming FCM payload
   - Detect type: emergency vs cancel
   - Trigger fullscreen alert activity for emergency
   - Route to cancel screen for cancel notifications

7. **mobile-google-services** - Download Google Services JSON
   - Download google-services.json from Firebase Console
   - Package name: com.safealert.app
   - Place in android/app/
   - Verify SHA fingerprints match

### Hardware Integration
8. **mobile-vibration** - Implement Vibration Pattern
   - Use vibrate package
   - Create SOS pattern: [500ms, 1000ms, 500ms, 1000ms, 500ms, 1000ms]
   - Repeat pattern 3 times
   - Handle permission denied gracefully

9. **mobile-flash** - Implement Flash/Torch
   - Use torch_light package
   - Create rapid red-white flash pattern (200ms interval)
   - Synchronize with vibration timing
   - Add graceful fallback if torch unavailable

10. **mobile-tts** - Implement Text-to-Speech
    - Use flutter_tts package
    - Convert alarm message to speech
    - Set language to Indonesian
    - Handle edge cases (very long messages)
    - Add fallback for TTS unavailable

### Personalization & Logic
11. **mobile-personalized-alert** - Implement Personalized Alert Logic
    - Create switch case for disability_type
    - **deaf**: Getar + Flash + Teks besar (NO TTS)
    - **blind**: TTS + Getar (NO flash)
    - **none**: All modalities (Getar + Flash + TTS + Teks)
    - Apply logic in fullscreen alarm screen
    - Store preference in SharedPreferences

### Emergency Features
12. **mobile-emergency-buttons** - Add Emergency Call Buttons
    - Add button to call 113 (Pemadam Kebakaran)
    - Add button to call 110 (Polisi)
    - Use url_launcher package with `tel:` scheme
    - Add button on home screen and alarm screen

### API & Backend Integration
13. **mobile-api-integration** - Implement API Client Service
    - Create api_service.dart for HTTP communication
    - Implement base URL configuration
    - Add POST /api/auth/register/ method
    - Add POST /api/confirm/ method
    - Add error handling & retry logic
    - Setup proper headers (Content-Type, User-Agent)

### Permissions & Configuration
14. **mobile-permissions** - Configure Android Permissions
    - Setup AndroidManifest.xml with required permissions:
      - INTERNET
      - VIBRATE
      - FLASHLIGHT
      - WAKE_LOCK (keep screen on during alarm)
      - POST_NOTIFICATIONS (Android 13+)
    - Add permission request UI for runtime permissions

### Build & Testing
15. **mobile-testing** - Build & Test APK Debug
    - Run `flutter build apk --debug`
    - Test on real Android device (not emulator)
    - Test registration workflow end-to-end
    - Test FCM reception and alarm display
    - Test vibration, flash, TTS for each disability type
    - Test confirmation submission
    - Test emergency call buttons
    - Verify all permissions work correctly

---

## 🎨 Phase 4: Dashboard Frontend (Dev 3)

**Goal:** Operator bisa login, verifikasi user, lihat daftar, trigger alarm, monitor confirmations

### Authentication & Layout
1. **dashboard-login** - Create Login Page
   - Build login.html with username/password form
   - Implement login view to verify credentials
   - Issue JWT token on successful login
   - Add error messaging (invalid credentials)
   - Setup session management

2. **dashboard-layout** - Build Dashboard Base Layout
   - Create base.html with responsive sidebar (fixed position, 280px width)
   - Setup navbar with logout and clock display
   - Create main content wrapper with proper margin-left (280px on desktop)
   - Apply Bootstrap 5 framework
   - Custom styling in dashboard.css
   - Fix table contrast (white text on dark background)
   - Test responsive layout on mobile

3. **dashboard-index** - Build Dashboard Summary Page
   - Create index.html showing statistics:
     - Total registered users
     - Pending verification count
     - Active alarms
     - Confirmation rate (confirmed / total)
   - Add live clock display
   - Add quick action buttons to each tab
   - Show last alarm timestamp

### User Management Tabs
4. **dashboard-verify-users** - Build User Verification Tab
   - Create verify_users.html with table of pending users
   - Display columns: Nama, No HP, Lantai, Tipe Disabilitas, Waktu Registrasi
   - Add green button "Verifikasi" (accept)
   - Add red button "Tolak" (reject)
   - Trigger PATCH /api/users/{id}/status/ on click
   - Show success/error feedback
   - Auto-remove row after action

5. **dashboard-user-list** - Build User List Tab
   - Create user_list.html with table of active users
   - Display columns: Nama, No HP, Lantai, Tipe Disabilitas, Admin Status, Konfirmasi Terakhir
   - Implement status dropdown (safe/evacuating/trapped/outside) - editable per row
   - Make phone numbers clickable: `<a href="tel:+628...">` for direct dialing
   - Implement AJAX update without page reload
   - Add loading spinner during update
   - Show success message after update

### Alarm Management Tab
6. **dashboard-alarm-send** - Build Alarm Send Section
   - Create UI component in alarms.html with textarea
   - Placeholder: "Ketik instruksi evakuasi... (contoh: KEBAKARAN LT. 7. GUNAKAN TANGGA TIMUR)"
   - Add large red button "KIRIM ALARM KE SEMUA USER"
   - Disable button if textarea is empty
   - Trigger POST /api/alarms/trigger/ on click
   - Show loading state + confirm modal before sending
   - Display number of recipients after send

7. **dashboard-alarm-history** - Build Alarm History Table
   - Create table showing alarm records with columns:
     - Waktu (timestamp)
     - Pesan (alarm message, truncated)
     - Admin (admin username who triggered)
     - Total (total users notified)
     - Konfirmasi (count confirmed / total)
     - Status (active/cancelled)
     - Aksi (Cancel button for active, disabled for cancelled)
   - Add sorting by timestamp (newest first)
   - Add pagination (10 rows per page)

8. **dashboard-detail-expand** - Implement Detail Expansion
   - When user clicks alarm row, expand to show detail
   - Display list of all users who received that alarm
   - Color code: Green = confirmed + their reported status, Yellow = not confirmed
   - Show comparison: Admin Status vs User Reported Status
   - Example: Admin says "Terjebak" but User says "Saya Aman"
   - Close detail when user clicks row again or clicks close button

### API Integration & Real-time Updates
9. **dashboard-api-integration** - Integrate with Backend API
   - Update all views to consume backend API endpoints
   - Include JWT token in Authorization header
   - Handle 401 redirect to login if token expired
   - Implement error handling: display user-friendly error messages
   - Add loading states (spinners, disabled buttons)
   - Implement response validation

10. **dashboard-realtime-update** - Add Real-time Update
    - Auto-refresh alarm confirmations every 5-10 seconds
    - Update confirmation count without full page reload
    - Use AJAX polling or WebSocket (polling easier for 24h hackathon)
    - Show "Last updated: 2 seconds ago" timestamp
    - Highlight newly confirmed users with animation/pulse

### Styling & Polish
11. **dashboard-styling** - Improve Dashboard Styling
    - Fix table styling: white text on dark/transparent background
    - Improve button colors: green (verify), red (cancel/alarm), blue (action)
    - Add smooth hover effects and transitions
    - Ensure sidebar and main content don't wrap on desktop
    - Optimize for mobile view (responsive sidebar toggle)
    - Add loading spinners for long operations
    - Improve form validation feedback
    - Add success/error toast notifications

### Testing & Validation
12. **dashboard-testing** - Test Dashboard Functionality
    - Test complete workflows:
      - Login → Verify user → Update status → Send alarm → View history
      - Expand alarm detail → View confirmation list
      - Cancel active alarm
    - Verify all links work (phone tel: links, status dropdowns)
    - Test with various user data (long names, international phone numbers)
    - Test concurrent updates (simulate multiple admins)
    - Performance test with 1000+ users in list
    - Fix all identified bugs

---

## 🔗 Phase 5-7: Integration, Testing & Deployment

**Goal:** End-to-end system works. Deployed and ready for demo.

### End-to-End Integration Testing
1. **integration-register-flow** - Test End-to-End Registration
   - Scenario: User register via mobile → Backend receive → Save to DB → Dashboard shows in pending → Admin verify → User becomes safe
   - Verify all database updates correct
   - Check JWT token generation
   - Validate user can immediately receive alarms after verification

2. **integration-alarm-flow** - Test End-to-End Alarm Flow
   - Scenario: Dashboard send alarm → Backend query users → FCM multicast → Mobile receive → Fullscreen alert muncul
   - Verify alarm reaches all active users
   - Test personalized alerts per disability type (deaf, blind, none)
   - Verify getar, flash, TTS triggered correctly for each type
   - Test with 10+ concurrent devices

3. **integration-confirm-flow** - Test End-to-End Confirmation
   - Scenario: Mobile user confirm status → Backend save → Dashboard auto-update
   - Test all 3 confirmation options: safe, trapped, evacuating
   - Verify confirmation appears immediately in dashboard
   - Test confirmation count increments correctly
   - Test confirmed user list shows correct status

4. **integration-cancel-flow** - Test End-to-End Cancel
   - Scenario: Dashboard cancel alarm → Backend send FCM cancel → Mobile receive → Green all-clear screen
   - Verify cancel notification reaches all users
   - Test all users' alarms stop immediately
   - Verify green screen displays and auto-dismisses
   - Test repeat alarm after cancel works correctly

5. **integration-cross-device** - Test Multi-Device Reception
   - Register 3+ devices with different disability types
   - Trigger alarm
   - Verify all devices receive simultaneously
   - Verify each device shows personalized alert
   - Test confirmation from all devices updates dashboard correctly
   - Test with network latency (simulate slow connection)

### Deployment & Infrastructure
6. **deploy-backend** - Deploy Backend to Production
   - Deploy Django app to Railway.app or Render.com (free tier)
   - Setup environment variables:
     - SECRET_KEY (generate new)
     - DATABASE_URL (PostgreSQL on Railway/Render)
     - Firebase credentials
     - DEBUG=False
   - Run migrations on production database
   - Test all endpoints on production URL
   - Setup error logging (Sentry optional)

7. **deploy-firebase** - Setup Firebase for Production
   - Create new Firebase project for production
   - Add Android app (com.safealert.app)
   - Generate google-services.json for release APK
   - Configure FCM settings and API quotas
   - Test FCM multicast delivery
   - Verify Firebase credentials loaded correctly

8. **deploy-apk-release** - Build Release APK
   - Generate signing key: `keytool -genkey -v -keystore safealert-release-key.jks ...`
   - Update android/key.properties with signing info
   - Build release APK: `flutter build apk --release`
   - Verify APK size reasonable
   - Test release APK on physical device (not debug)
   - Upload APK to shared storage for demo devices

9. **deploy-git-tag** - Create Release Tag
   - Commit all final code to main branch
   - Create git tag: `git tag v1.0-hackathon`
   - Push tag to GitHub: `git push origin v1.0-hackathon`
   - Include release notes in GitHub releases
   - Tag commit should include setup documentation

### Demo Preparation
10. **demo-preparation** - Prepare 3-Minute Demo Script
    - Document demo flow:
      1. Show dashboard login
      2. Register new user via mobile app (live or pre-recorded)
      3. Admin verify user in dashboard
      4. Admin trigger alarm message
      5. Mobile receive fullscreen alert with personalized features
      6. User confirm status
      7. Show confirmation in dashboard
      8. Admin cancel alarm
      9. Mobile show all-clear screen
    - Prepare talking points for each step
    - Setup backup devices and USB cables
    - Charge all devices to 100%
    - Prepare personal hotspot / WiFi backup

11. **demo-testing** - Final Demo & Edge Case Testing
    - Run complete demo scenario 3-5 times (iron out timing)
    - Test edge cases:
      - Invalid phone number input
      - Missing floor field
      - Network latency/disconnect
      - Quick multiple alarms
      - Fast consecutive confirmations
      - Device screen lock during alarm
      - Very long alarm message (truncation)
    - Prepare contingency plans for common failures
    - Record demo video as backup

---

## 💡 Phase 8+: Future Enhancements

**Goal:** Production-grade features for next iteration.

### Location & Smart Alerts
1. **future-gps-detection** - Implement GPS Floor Detection
   - Add GPS coordinates to building floors
   - Auto-detect user's current floor via GPS on entry
   - Setup BLE beacons per floor for more accuracy
   - Reduce manual floor input errors
   - Show current location on dashboard map

2. **future-integration-cctvapi** - Integrate with CCTV/Sensor Systems
   - Connect to building CCTV monitoring system API
   - Integrate smoke/fire/motion sensors
   - Auto-trigger alarms based on detected hazards
   - Remove dependency on manual operator input
   - Faster response to emergencies

### Token & Notification Management
3. **future-token-cleanup** - Setup Dead Token Cleanup
   - Implement job to detect zombie FCM tokens
   - Remove tokens from devices that uninstalled app
   - Reduce FCM delivery failures and overhead
   - Track token death rates per user cohort
   - Auto-retry registration on app reinstall

4. **future-sms-fallback** - Add SMS Fallback Integration
   - Integrate Twilio SMS API
   - On FCM failure, automatically send SMS alert
   - SMS should include: hazard type, floor affected, evacuation route
   - Track SMS delivery rates
   - Implement SMS confirmation (user replies with status)
   - Fallback for users without app installed

### Platform Expansion
5. **future-ios-support** - Add iOS Support
   - Port Flutter app to iOS
   - Handle iOS Critical Alert permission (requires review)
   - Implement iOS-specific audio patterns
   - Build iOS release app + upload to App Store
   - Test on iPhone/iPad devices
   - Coordinate Apple review process

### Analytics & Insights
6. **future-analytics** - Build Analytics Dashboard
   - Metrics: alarm response time, confirmation rate per user
   - Heatmaps: high-risk zones, repeat incidents
   - Trends: false alarm rate, time-to-evacuation
   - User engagement: app active users, notification interaction
   - Export reports (PDF/CSV)
   - Real-time anomaly detection

### Localization & Accessibility
7. **future-multi-language** - Implement Multi-Language Support
   - Setup i18n (internationalization) framework
   - Add languages: Indonesian (id), English (en), Regional (Sundanese, Javanese)
   - Translation files for mobile app and dashboard
   - Adapt date/time formats per locale
   - Test with native speakers

8. **future-audio-beacon** - Implement Audio Beacon
   - Add directional audio guidance system
   - Guide blind users toward safe exit
   - Use spatial audio (stereo panning)
   - Integrate with building safe exit routing API
   - Test with blind users for usability

### Advanced Communication
9. **future-twoway-sos** - Add Two-Way SOS Communication
   - Implement video/audio call from mobile to emergency center
   - Live location tracking during evacuation
   - Emergency operator can see user's real-time location
   - Support for operator to send targeted instructions
   - Record all calls for incident review

### Visualization & Navigation
10. **future-building-map** - Add Interactive Building Map
    - Display building floor plan (CAD import)
    - Show real-time user locations during alarm (opt-in privacy)
    - Highlight safe exits and assembly points
    - Show evacuation routes on map
    - Calculate optimal routes for each user
    - Mobile app shows turn-by-turn directions

---

## 📈 Progress Tracking

### Completion Metrics
- **Backend Completion:** 0/12 todos
- **Mobile Completion:** 0/15 todos
- **Dashboard Completion:** 0/12 todos
- **Integration Completion:** 0/11 todos
- **Overall:** 0/60 todos (0%)

### Dependencies Between Phases
```
Phase 2 (Backend) ← Must complete before Phase 3 & 4
         ↓
Phase 3 (Mobile) ← Depends on Phase 2 API
Phase 4 (Dashboard) ← Depends on Phase 2 API
         ↓
Phase 5-7 (Integration & Deploy) ← Depends on Phase 2, 3, 4
         ↓
Phase 8+ (Enhancements) ← Optional after MVP
```

---

## 🎯 Success Criteria

### MVP Acceptance Criteria
- ✅ All 60 todos marked as done
- ✅ End-to-end flow tested and working
- ✅ All 3 disability types tested (deaf, blind, non-disabilitas)
- ✅ Dashboard operator can login and control alarms
- ✅ Mobile users receive personalized alerts
- ✅ Confirmations tracked and displayed in dashboard
- ✅ Backend deployed and accessible from internet
- ✅ Release APK built and tested on real device
- ✅ Demo runs successfully without technical glitches

### Quality Standards
- ✅ All API endpoints return correct HTTP status codes
- ✅ Error messages are clear and helpful
- ✅ UI is responsive (mobile-friendly)
- ✅ No unhandled exceptions
- ✅ FCM multicast works with 1000+ tokens
- ✅ Database queries optimized (no N+1 problems)
- ✅ Code committed to GitHub with meaningful messages

---

**Next Steps:**
1. Review and approve this todo list
2. Assign todos to team members (Dev 1, 2, 3)
3. Start with Phase 2 backend foundation
4. Use daily standup to track progress
5. Escalate blockers immediately

**Questions?** Refer back to SAFEALERT_DOKUMENTASI_LENGKAP.md for architecture details.

