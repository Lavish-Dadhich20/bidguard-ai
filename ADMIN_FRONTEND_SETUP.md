# BidGuard AI - Admin/Tender/Bidder Frontend Update

## What changed
- Separate Admin, Tender and Bidder navigation.
- Role-specific dashboards.
- Removed bidder management/compliance/verification pages from Tender portal.
- Removed bidder Compliance Dashboard from Admin portal.
- Added standard 13 core compliance requirements to New Tender.
- New Tender saves structured requirements into `tenders.requirements`.
- Tender Analytics now reads real verification report data.
- Reports are role-aware; bidders only see their own reports.
- Admin Verification Results shows all verification records and details.
- Audit Trail object rendering crash fixed by safely formatting API objects.
- API error objects are now converted to readable messages instead of `[object Object]`.
- Added Admin `+ Add Bidder` workflow.
- New bidder uses the 10-digit mobile number as the login username.
- Existing document/extractor validation flow was not changed.

## One-time Supabase step
Run this file in Supabase SQL Editor:

`bidguard_compliance_integrated_latest_extractor_fixed_v3/bidguard_compliance_integrated_latest_extractor_fixed_v2/bidguard_compliance_integrated_latest_extractor_fixed/bidguard_compliance_final/admin_frontend_migration.sql`

This adds the tender metadata fields and bidder login metadata used by the new workflow.

## Backend restart
After replacing `api_server.py`, restart the existing FastAPI server.

## Frontend
Keep the existing frontend `.env` file. Do not replace it with a public copy.

Then in `frontend`:

```powershell
npm run build
npm run dev
```

The checked source passes TypeScript compilation. The Linux packaging environment could not run Vite because the uploaded `node_modules` contains Windows-native Rollup dependencies; the normal Windows `npm run build` should use the project's existing Windows dependencies.

## New bidder login
1. Admin opens **Bidder Management**.
2. Clicks **Add Bidder**.
3. Enters bidder name, company, email, mobile number and password.
4. The mobile number becomes the login username.
5. On the login screen choose **Use Backend Login**.
6. Enter the mobile number and password.

## Important
Do not replace the existing extractor, compliance engine, document validation logic, or backend `.env` secret.
