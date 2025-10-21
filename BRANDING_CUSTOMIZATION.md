# 1BIP Branding Customization Guide

This document describes all the branding changes made to customize CompreFace for the 1BIP organization and where to place your custom logo files.

## ✅ Completed Branding Changes

### 1. Main Application Title
- **File**: `README.md`
- **Changes**: Updated main title and descriptions to "1BIP Face Recognition & Attendance System"

### 2. UI Page Title
- **File**: `ui/src/index.html` (line 21)
- **Change**: `<title>1BIP Face Recognition System</title>`

### 3. UI Translations & Text
- **File**: `ui/src/assets/i18n/en.json`
- **Changes**:
  - Line 79: Logo alt text → "1BIP Face Recognition System"
  - Line 91: Application description references
  - Line 188: User management text
  - Line 213: User info text
  - Line 231: Application users text
  - Line 354: Loading screen → "1BIP Face Recognition System is starting ..."

### 4. Configuration File
- **File**: `.env`
- **Changes**:
  - Added 1BIP header comments
  - Updated database name: `frs_1bip`
  - Updated database password: `1BIP_SecurePassword_2025` (change in production!)
  - Added organization-specific comments

### 5. Sign-up Form
- **File**: `ui/src/app/features/sign-up-form/sign-up-form.component.html`
- **Change**: Removed external CompreFace documentation link

---

## 🎨 Logo Replacement Instructions

To complete the branding, replace the following logo files with your 1BIP organization logos:

### Primary Logo Files (MUST REPLACE)

#### 1. Main Application Logo
**Location**: `ui/src/assets/img/face-recognition-logo.svg`
- Used in the main application header/toolbar
- **Format**: SVG (recommended) or PNG
- **Recommended size**: Width ~200px, maintain aspect ratio
- **Usage**: Desktop header logo

#### 2. Mobile Logo
**Location**: `ui/src/assets/img/face-recognition-logo-mobile.svg`
- Used in mobile responsive view
- **Format**: SVG (recommended) or PNG
- **Recommended size**: Width ~150px, maintain aspect ratio
- **Usage**: Mobile header logo

#### 3. Mobile Login Logo
**Location**: `ui/src/assets/img/face-recognition-logo-mobile-login.svg`
- Used on the mobile login/sign-up screens
- **Format**: SVG (recommended) or PNG
- **Recommended size**: Width ~150px, maintain aspect ratio
- **Usage**: Mobile login/registration pages

### Secondary Logo Files (OPTIONAL)

#### 4. Standard Logo (PNG)
**Location**: `ui/src/assets/img/logo.png`
- Fallback logo in PNG format
- **Format**: PNG
- **Recommended size**: 200x50px or similar

#### 5. Blue Logo Variant
**Location**: `ui/src/assets/img/logo_blue.png`
- Alternative color variant
- **Format**: PNG
- **Recommended size**: 200x50px or similar

### Browser Icon (Favicon)

#### 6. Favicon
**Location**: `ui/src/favicon.ico`
- Browser tab icon
- **Format**: ICO (recommended) or PNG
- **Required size**: 16x16px and 32x32px (ICO can contain multiple sizes)
- **Usage**: Browser tab, bookmarks

---

## 📝 How to Replace Logos

### Option 1: Direct File Replacement (Recommended)
1. Prepare your 1BIP logos in the appropriate formats (SVG for scalability)
2. Name them exactly as listed above
3. Replace the files in the specified locations
4. Rebuild the Docker containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

### Option 2: Keep Original Names, Update References
1. Place your logo files in `ui/src/assets/img/`
2. Update references in the following files:
   - Search for logo references in Angular components
   - Update `<img>` tags pointing to old logo paths

---

## 🔧 Additional Customization Options

### Email Templates
If you enable email server (`enable_email_server=true` in `.env`), you may want to customize:
- **Location**: `java/admin/src/main/resources/templates/`
- Email templates for user registration, password reset, etc.

### Theme Colors
To match 1BIP's brand colors:
- **Location**: `ui/src/styles/` (SCSS files)
- Update CSS variables and theme colors
- Main theme file: `ui/src/styles.scss`

### Application Name in Java Backend
If you want to update backend references:
- Search for "CompreFace" in `java/admin/` and `java/api/` directories
- Update configuration files, property files, and comments

---

## 🚀 Building with Custom Branding

After making all branding changes:

```bash
# Stop existing containers
docker-compose down

# Rebuild with new branding
docker-compose build --no-cache

# Start the system
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 📋 Branding Checklist

Use this checklist to ensure complete branding:

- [x] Updated README.md title and descriptions
- [x] Updated UI page title (index.html)
- [x] Updated UI translations (en.json)
- [x] Updated .env configuration with 1BIP settings
- [x] Removed external CompreFace links
- [ ] **Replace main logo SVG** (`face-recognition-logo.svg`)
- [ ] **Replace mobile logo SVG** (`face-recognition-logo-mobile.svg`)
- [ ] **Replace mobile login logo SVG** (`face-recognition-logo-mobile-login.svg`)
- [ ] **Replace favicon** (`favicon.ico`)
- [ ] Replace optional PNG logos
- [ ] Update theme colors (optional)
- [ ] Customize email templates (if using email)
- [ ] Test on desktop browser
- [ ] Test on mobile browser
- [ ] Test logo appearance in different themes/modes

---

## 🔒 Security Reminder

**IMPORTANT**: The `.env` file now contains a placeholder password. Before deploying to production:

1. Change `postgres_password` in `.env` to a strong, unique password
2. Configure email settings if enabling email server
3. Set up proper SSL/TLS certificates for HTTPS
4. Review and update OAuth2 client secret in `java/admin/src/main/resources/application.yml`

---

## 📞 Need Help?

For technical assistance with customization:
- Review CompreFace documentation: https://github.com/exadel-inc/CompreFace/tree/master/docs
- Check the original project for updates: https://github.com/exadel-inc/CompreFace

---

**Last Updated**: 2025-10-21
**Customized for**: 1BIP Organization
**Based on**: CompreFace v1.2.0 (Apache 2.0 License)
