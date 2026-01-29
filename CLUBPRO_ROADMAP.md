# ClubPro - Roadmap: Shop, Landing Page & Enhanced Socios Control

## 🎯 Goals

Deliver immediate value to the club with:

1. **Online Shop** - Sell products, merchandise, memberships
2. **Enhanced Landing Page** - Better conversion, showcase value
3. **Advanced Socios Control** - More management power, member self-service

---

## 🛒 Phase 1: Online Shop

### Features to Build

#### 1.1 Core Shop Models

- **Product** - Name, description, price, stock, images, categories
- **Category** - Product categories (Merchandise, Books, Equipment, etc.)
- **Cart** - Session-based shopping cart
- **CartItem** - Individual items in cart
- **Order** - Customer orders
- **OrderItem** - Items in each order
- **Payment** - Payment tracking (PIX, credit card, etc.)

#### 1.2 Shop Views

- Product listing with filters
- Product detail page
- Shopping cart management
- Checkout process
- Order history (for logged-in users)
- Admin product management

#### 1.3 Payment Integration

- PIX payment (QR code generation)
- Credit card (via payment gateway - Mercado Pago or similar)
- Payment status tracking
- Order confirmation emails

#### 1.4 Shop Features

- Stock management
- Product variants (sizes, colors)
- Discount codes/coupons
- Member discounts (for socios)
- Product reviews/ratings (future)

---

## 🎨 Phase 2: Enhanced Landing Page

### Improvements

#### 2.1 Real Statistics

- Replace placeholder stats with real data:
  - Actual member count
  - Real tournament count
  - Active members this month
  - Revenue statistics

#### 2.2 Social Proof

- Testimonials section
- Member success stories
- Recent tournament winners
- Club achievements

#### 2.3 Better CTAs

- Clear value propositions
- Multiple conversion points
- Shop preview section
- Membership benefits showcase

#### 2.4 Content Sections

- About the club
- Upcoming events calendar
- Featured products from shop
- Member benefits explained

---

## 👥 Phase 3: Enhanced Socios Control

### Admin Features

#### 3.1 Bulk Actions

- Bulk status update (ativo/inadimplente/suspenso)
- Bulk export to CSV/Excel
- Bulk email/SMS sending
- Bulk payment registration
- Bulk document upload

#### 3.2 Advanced Filtering

- Filter by status, plan, payment status
- Filter by date ranges (association, expiration)
- Filter by location (city, state)
- Filter by rating (FIDE, CBX)
- Save filter presets

#### 3.3 Advanced Search

- Full-text search across all fields
- Search by CPF, email, phone
- Search by member number
- Recent searches history

#### 3.4 Reporting Enhancements

- Custom date range reports
- Export reports to PDF/Excel
- Scheduled reports (email)
- Member growth charts
- Revenue analytics

### Member Portal (Self-Service)

#### 3.5 Member Dashboard

- View own profile
- View payment history
- View documents
- View membership status
- Upcoming payment reminders

#### 3.6 Self-Service Features

- Update contact information
- Upload documents
- Request membership changes
- View club events/tournaments
- Access member-only content

#### 3.7 Notifications

- Email notifications for:
  - Payment reminders
  - Membership expiration
  - Document requests
  - Club announcements
- SMS notifications (optional)

---

## 📅 Implementation Timeline

### Week 1: Shop Foundation

- ✅ Create shop app
- ✅ Build core models (Product, Category, Cart, Order)
- ✅ Basic product listing and detail pages
- ✅ Shopping cart functionality

### Week 2: Shop Completion

- ✅ Checkout process
- ✅ Payment integration (PIX first)
- ✅ Order management
- ✅ Admin product management

### Week 3: Landing Page & Socios Enhancements

- ✅ Enhanced landing page
- ✅ Bulk actions for socios
- ✅ Advanced filtering
- ✅ Member portal foundation

### Week 4: Polish & Launch

- ✅ Member self-service features
- ✅ Email notifications
- ✅ Testing and bug fixes
- ✅ Documentation

---

## 🛠️ Technical Stack

### New Dependencies Needed

```python
# Shop
django-crispy-forms  # Better forms
Pillow  # Image handling (already have)
qrcode  # PIX QR codes
mercadopago  # Payment gateway (optional)

# Reports
openpyxl  # Excel export
reportlab  # PDF generation

# Notifications
django-email-backends  # Email
celery  # Async tasks (optional)
```

### App Structure

```
clubpro/
├── shop/              # NEW - Online shop
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── templates/
├── socios/            # ENHANCE - More features
│   └── (existing + new views)
└── users/             # ENHANCE - Landing page
    └── templates/
```

---

## 💡 Quick Wins (Can Start Immediately)

1. **Add real stats to landing page** - 30 minutes
2. **Add bulk status update** - 1 hour
3. **Add advanced search** - 2 hours
4. **Create member portal view** - 2 hours
5. **Add export to CSV** - 1 hour

---

## 🎯 Success Metrics

### Shop

- Products added to shop
- Orders processed
- Revenue generated
- Member discounts used

### Landing Page

- Conversion rate (visitors → signups)
- Time on page
- CTA clicks

### Socios Control

- Time saved on bulk operations
- Member self-service usage
- Reduced support requests
- Better data insights

---

## 🚀 Let's Start!

Ready to begin implementation. Starting with:

1. Shop app foundation
2. Quick wins for socios
3. Landing page improvements
