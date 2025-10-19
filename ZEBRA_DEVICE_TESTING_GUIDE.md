# 📱 Zebra Device Testing Guide - Sprint WMS Phase 1

**Version:** 1.0  
**Date:** October 19, 2025  
**Devices:** Zebra TC21, TC26, MC3300  
**PWA:** Magacin Track Worker App

---

## 🎯 Testing Objectives

Verify that the Manhattan-style PWA works flawlessly on Zebra Android handheld devices with:
- ✅ Tap targets >= 48px (touch-friendly)
- ✅ Text readable (min 14px font)
- ✅ PWA installable
- ✅ Offline queue functional
- ✅ Barcode scanner integration
- ✅ Battery-efficient
- ✅ Serbian language display

---

## 📱 Target Devices

### Zebra TC21/TC26
- **Screen:** 5.5" HD+ (1280 x 720 pixels)
- **OS:** Android 10+
- **Scanner:** Integrated 1D/2D barcode scanner
- **Touch:** Capacitive multi-touch
- **Battery:** 3100 mAh
- **RAM:** 3-4 GB

### Zebra MC3300
- **Screen:** 4" WVGA (800 x 480 pixels)
- **OS:** Android 7-10
- **Scanner:** Integrated 1D/2D barcode scanner
- **Touch:** Capacitive
- **Battery:** 4800 mAh
- **RAM:** 2-4 GB

---

## ✅ Pre-Test Checklist

### Device Setup

- [ ] Device charged (>50%)
- [ ] WiFi connected to network
- [ ] System updates applied
- [ ] Chrome browser updated
- [ ] Developer options enabled (for debugging)
- [ ] USB debugging enabled (optional)
- [ ] Screen brightness set to 50%

### PWA Configuration

- [ ] PWA deployed to accessible URL
- [ ] HTTPS enabled (or localhost for testing)
- [ ] Service worker registered
- [ ] Manifest.json accessible
- [ ] Icons (192x192, 512x512) available

---

## 🧪 Test Cases

### Test 1: PWA Installation

**Objective:** Verify PWA can be installed on Zebra device

**Steps:**
1. Open Chrome browser on Zebra device
2. Navigate to PWA URL (e.g., http://192.168.1.100:5131)
3. Wait for "Add to Home Screen" prompt
4. Tap "Install" or "Add"
5. Verify app icon appears on home screen
6. Launch app from home screen
7. Verify app opens in fullscreen mode (no browser UI)

**Expected Results:**
- ✅ Install prompt appears within 5 seconds
- ✅ Installation completes successfully
- ✅ Icon with correct logo appears
- ✅ App launches in standalone mode
- ✅ No browser chrome visible

**Pass Criteria:**
- All expected results met
- Installation time < 10 seconds

---

### Test 2: Manhattan Header Display

**Objective:** Verify header renders correctly on Zebra screen

**Steps:**
1. Launch PWA
2. Login with worker credentials
3. Observe Manhattan Header

**Checklist:**
- [ ] Avatar visible with correct initials
- [ ] Full name readable (font size adequate)
- [ ] Role displayed in Serbian
- [ ] Shift badge shows if team assigned
- [ ] Shift time visible (08:00-15:00 or 12:00-19:00)
- [ ] Pause info visible
- [ ] Online/Offline indicator shows
- [ ] Logout button accessible
- [ ] Header height appropriate (not too tall)
- [ ] No text cutoff or overlap

**TC21/TC26 (1280x720):**
- [ ] All elements fit on screen
- [ ] Spacing comfortable
- [ ] Text size: 14-16px minimum

**MC3300 (800x480):**
- [ ] Elements may wrap but remain visible
- [ ] Text size: 13-14px minimum
- [ ] All interactive elements accessible

---

### Test 3: Home Page Grid Layout

**Objective:** Verify grid cards are touch-friendly

**Steps:**
1. Navigate to home page (after login)
2. Observe grid layout

**Checklist:**
- [ ] Cards display in 2-column grid
- [ ] Each card >= 120px height
- [ ] Icons visible and clear (40-48px)
- [ ] Labels in Serbian
- [ ] Task count badge shows (if > 0)
- [ ] White/light grey background
- [ ] Cards respond to tap (hover effect)
- [ ] No scrolling issues

**Touch Test:**
- [ ] Can tap each card with thumb
- [ ] No accidental double-taps
- [ ] Tap target feels comfortable
- [ ] Visual feedback on tap (highlight/shadow)

**TC21/TC26:**
- [ ] 2-column grid comfortable
- [ ] Card min-height: 140px
- [ ] Icons: 48px

**MC3300:**
- [ ] 2-column grid still works
- [ ] Card min-height: 120px
- [ ] Icons: 40px (smaller but visible)

---

### Test 4: Quantity Stepper (Tap Targets)

**Objective:** Verify large stepper buttons are easily tappable

**Steps:**
1. Navigate to task detail page
2. Find quantity stepper component

**Checklist:**
- [ ] Minus button: 64px x 64px (TC21/TC26) or 52px x 52px (MC3300)
- [ ] Plus button: same as minus
- [ ] Input field: large font (32px on TC21, 24px on MC3300)
- [ ] Unit label visible
- [ ] Max quantity displayed
- [ ] Buttons respond to single tap
- [ ] No accidental double-increments
- [ ] Visual feedback on tap

**Tap Test (10 times):**
- [ ] Can accurately tap +/- buttons with gloved hand
- [ ] Can tap with thumb nail
- [ ] No mis-taps
- [ ] Responsive feel (immediate feedback)

---

### Test 5: Partial Completion Modal

**Objective:** Verify modal is usable on small screen

**Steps:**
1. Enter količina < tražena
2. Click "Završi zadatak"
3. Observe modal

**Checklist:**
- [ ] Modal centers on screen
- [ ] Warning alert visible
- [ ] Article name readable
- [ ] Količina tražena/pronađena displayed
- [ ] % ispunjenja shown
- [ ] Razlog dropdown tappable
- [ ] Dropdown options readable (font >= 14px)
- [ ] TextArea for "Drugo" comfortable to type
- [ ] Buttons: "Otkaži" and "Potvrdi" >= 48px height
- [ ] Can tap buttons accurately

**TC21/TC26:**
- [ ] Modal width comfortable (max 500px)
- [ ] All content visible without scroll

**MC3300:**
- [ ] Modal may scroll, but buttons always visible
- [ ] Dropdown accessible

---

### Test 6: Offline Queue

**Objective:** Verify offline queue works on Zebra

**Steps:**
1. With PWA open and logged in
2. Enable Airplane mode on Zebra device
3. Complete a task partially
4. Observe offline banner
5. Disable Airplane mode
6. Observe sync

**Checklist:**
- [ ] Offline banner appears immediately
- [ ] Partial completion saved to IndexedDB
- [ ] No error messages
- [ ] UI shows "Čeka sinhronizaciju" status
- [ ] When online, auto-sync triggers
- [ ] Success message after sync
- [ ] Admin table reflects change
- [ ] No duplicate entries

**IndexedDB Verification:**
```javascript
// Chrome DevTools > Application > IndexedDB
// Database: magacin-offline-queue
// Store: actions
// Check for pending action
```

---

### Test 7: Barcode Scanner Integration

**Objective:** Verify barcode scanner triggers properly

**Steps:**
1. Navigate to task detail
2. Tap "Skeniraj barkod" button
3. Scan a barcode using Zebra scanner

**Checklist:**
- [ ] Scanner activates (red laser or camera)
- [ ] Barcode scan triggers input event
- [ ] Scanned code appears in input field
- [ ] Quantity auto-increments (if configured)
- [ ] Can manually edit scanned code
- [ ] Can re-scan if mistake

**Scanner Types:**
- [ ] Works with Zebra imager (2D)
- [ ] Works with Zebra laser (1D)

---

### Test 8: Performance on Zebra

**Objective:** Verify app performance is acceptable

**Metrics:**
- [ ] Page load time < 3 seconds
- [ ] Navigation transition < 500ms
- [ ] Scroll smoothness (60 FPS)
- [ ] Tap response time < 100ms
- [ ] No lag when typing
- [ ] Memory usage < 200 MB
- [ ] Battery drain acceptable (< 10%/hour)

**Load Test:**
```bash
# Open task list with 20+ tasks
# Scroll through list
# Check for lag or stuttering
# Expected: Smooth scrolling
```

---

### Test 9: Battery Efficiency

**Objective:** Ensure PWA doesn't drain battery

**Steps:**
1. Fully charge Zebra device
2. Launch PWA
3. Use app for 30 minutes (normal workflow)
4. Check battery percentage

**Checklist:**
- [ ] Battery drain < 5% in 30 minutes
- [ ] No excessive CPU usage
- [ ] WebSocket doesn't prevent sleep
- [ ] Background sync reasonable

**Optimization Verification:**
- [ ] Service worker registered (reduces network)
- [ ] Images optimized/compressed
- [ ] No auto-playing videos
- [ ] Polling interval reasonable (15s+)

---

### Test 10: Serbian Language Display

**Objective:** Verify Serbian characters display correctly

**Checklist:**
- [ ] Latin characters display correctly
- [ ] Special characters (č, ć, š, đ, ž) display
- [ ] No encoding issues (�)
- [ ] Font supports Serbian glyphs
- [ ] Dates formatted correctly (dd.mm.yyyy)
- [ ] Numbers formatted correctly (1.234,56)

**Test Strings:**
- "Završeno (djelimično)"
- "Nema na stanju"
- "Oštećeno"
- "Nije pronađeno"
- "Količina pronađena"

---

### Test 11: High Contrast Mode

**Objective:** Verify visibility in warehouse lighting

**Steps:**
1. Enable high contrast mode (if supported)
2. Or manually test in bright warehouse environment

**Checklist:**
- [ ] Text readable in bright light
- [ ] Buttons clearly visible
- [ ] Color contrast ratio >= 4.5:1 (WCAG AA)
- [ ] No washed-out colors
- [ ] Icons have sufficient weight

**Test in:**
- [ ] Direct sunlight
- [ ] Fluorescent warehouse lighting
- [ ] Low light/evening

---

## 📊 Test Results Template

```markdown
## Zebra Test Results - [Device Model]

**Date:** _______________
**Tester:** _______________
**Device:** Zebra TC21 / TC26 / MC3300
**OS Version:** Android __
**PWA Version:** 1.0
**Network:** WiFi / LTE

### Test Results

| Test | Result | Notes |
|------|--------|-------|
| PWA Installation | ✅ PASS / ❌ FAIL | |
| Manhattan Header | ✅ PASS / ❌ FAIL | |
| Home Grid | ✅ PASS / ❌ FAIL | |
| Quantity Stepper | ✅ PASS / ❌ FAIL | |
| Partial Modal | ✅ PASS / ❌ FAIL | |
| Offline Queue | ✅ PASS / ❌ FAIL | |
| Barcode Scanner | ✅ PASS / ❌ FAIL | |
| Performance | ✅ PASS / ❌ FAIL | |
| Battery Life | ✅ PASS / ❌ FAIL | |
| Serbian Language | ✅ PASS / ❌ FAIL | |
| High Contrast | ✅ PASS / ❌ FAIL | |

### Issues Found

1. [Issue description]
   - Severity: Critical / Major / Minor
   - Steps to reproduce:
   - Expected:
   - Actual:

### Screenshots

[Attach screenshots here]

### Overall Assessment

- [ ] ✅ APPROVED - Ready for production
- [ ] ⚠️ CONDITIONAL - Minor fixes needed
- [ ] ❌ REJECTED - Major issues found

**Sign-off:** _______________
```

---

## 🔧 Troubleshooting

### Issue: PWA Won't Install

**Solution:**
```bash
# Check manifest.json
curl http://your-pwa-url/manifest.json

# Verify HTTPS (required for PWA except localhost)
# Check service worker registration
# Browser Console > Application > Service Workers

# Clear browser data and retry
```

### Issue: Tap Targets Too Small

**Solution:**
```css
/* Increase tap target size in CSS */
.manhattan-grid-card {
  min-height: 140px; /* Increase from 120px */
}

.quantity-stepper__button {
  min-width: 68px !important; /* Increase from 64px */
  height: 68px !important;
}
```

### Issue: Text Too Small on MC3300

**Solution:**
```css
/* Add MC3300-specific media query */
@media (max-width: 480px) and (max-height: 480px) {
  body {
    font-size: 15px; /* Increase base font */
  }
  
  .manhattan-header__name {
    font-size: 16px; /* Increase from 15px */
  }
}
```

### Issue: Scanner Not Triggering

**Solution:**
```javascript
// Listen for DataWedge intent
document.addEventListener('DOMContentLoaded', () => {
  if (window.Android && window.Android.onBarcodeScanned) {
    window.Android.onBarcodeScanned = (barcode) => {
      // Handle scanned barcode
      handleBarcodeInput(barcode);
    };
  }
});
```

---

## 📋 Acceptance Criteria

### For Production Release:

- [ ] All 11 test cases PASS on TC21
- [ ] All 11 test cases PASS on MC3300
- [ ] No critical issues found
- [ ] Performance acceptable (< 3s load time)
- [ ] Battery drain acceptable (< 10%/hour)
- [ ] 10/10 accuracy on tap tests
- [ ] Serbian language perfect
- [ ] Offline queue 100% reliable

### Manhattan Design Compliance:

- [ ] Tap targets >= 48px verified
- [ ] Font sizes >= 14px verified
- [ ] High contrast verified (4.5:1 ratio)
- [ ] White background throughout
- [ ] Monochrome icons
- [ ] Consistent spacing (8px grid)

---

## 🚀 Test Execution

### Quick Test (30 minutes)

1. Install PWA on Zebra (5 min)
2. Test navigation (5 min)
3. Test partial completion flow (10 min)
4. Test offline queue (5 min)
5. Test barcode scanner (5 min)

### Comprehensive Test (2 hours)

1. All 11 test cases above
2. Battery life test (30 min use)
3. Performance profiling
4. Memory leak detection
5. Edge cases (no network, low battery, etc.)

---

## 📊 Test Metrics

### Target Metrics:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Install Success Rate | 100% | 10/10 installs successful |
| Tap Accuracy | >95% | 95/100 taps hit target |
| Load Time (3G) | <5s | Chrome DevTools Network |
| Scroll FPS | >50 | Chrome DevTools Performance |
| Memory Usage | <200 MB | Chrome DevTools Memory |
| Battery Drain | <10%/hour | Device settings |
| Offline Queue Success | 100% | 10/10 syncs successful |

---

## 📸 Screenshot Checklist

Required screenshots for documentation:

### PWA Screens:
- [ ] Login page (portrait)
- [ ] Manhattan Header (closeup)
- [ ] Home page grid (full screen)
- [ ] Task list page
- [ ] Task detail with quantity stepper
- [ ] Partial completion modal
- [ ] Offline banner
- [ ] Serbian language examples

### Device Tests:
- [ ] PWA icon on home screen
- [ ] App in fullscreen mode
- [ ] Barcode scanner activated
- [ ] Offline queue in DevTools

### Comparisons:
- [ ] TC21 vs MC3300 (same page)
- [ ] Portrait vs landscape
- [ ] Day vs night mode

---

## ✅ Final Approval

### Device Compatibility Matrix

| Feature | TC21/TC26 | MC3300 | Notes |
|---------|-----------|---------|-------|
| PWA Installation | ✅ / ❌ | ✅ / ❌ | |
| Manhattan Header | ✅ / ❌ | ✅ / ❌ | |
| Home Grid | ✅ / ❌ | ✅ / ❌ | |
| Quantity Stepper | ✅ / ❌ | ✅ / ❌ | |
| Partial Modal | ✅ / ❌ | ✅ / ❌ | |
| Offline Queue | ✅ / ❌ | ✅ / ❌ | |
| Barcode Scanner | ✅ / ❌ | ✅ / ❌ | |
| Performance | ✅ / ❌ | ✅ / ❌ | |
| Battery Life | ✅ / ❌ | ✅ / ❌ | |
| Serbian Display | ✅ / ❌ | ✅ / ❌ | |

### Overall Assessment:

- [ ] ✅ **APPROVED** - Ready for production on Zebra devices
- [ ] ⚠️ **CONDITIONAL** - Minor fixes needed (list below)
- [ ] ❌ **REJECTED** - Major issues prevent deployment

**Issues to Fix:**
1. _______________
2. _______________
3. _______________

**Tested By:** _______________  
**Date:** _______________  
**Sign-off:** _______________

---

## 🎓 Tips for Zebra Testing

### Best Practices:

1. **Test with gloves** - Many warehouse workers wear gloves
2. **Test in actual warehouse** - Temperature, lighting conditions matter
3. **Test battery drain** - 8-hour shift simulation
4. **Test with multiple users** - Concurrent device testing
5. **Test drop scenarios** - Ensure PWA persists after crash

### Common Issues:

**Touch sensitivity:**
- Zebra devices may have less sensitive touch than consumer phones
- Increase tap target padding if needed

**Screen brightness:**
- Auto-brightness may reduce visibility
- Test at various brightness levels

**Scanner integration:**
- Some Zebra devices use DataWedge
- Configure DataWedge profile for PWA

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Status:** Ready for Zebra device testing


