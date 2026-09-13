# PurohitConnect

A comprehensive platform connecting devotees with purohits for religious ceremonies and services. It includes the Django website and the Flutter devotee app.

## Features

- **User Authentication**: OTP-based login/signup with SMS verification
- **Purohit Discovery**: Search and filter purohits by location, services, and ratings
- **Booking System**: Real-time availability checking and booking management
- **Payment Integration**: Wallet system with Razorpay integration for secure payments
- **Mixed Checkout**: Pay partially from wallet and remainder via Razorpay
- **Admin Dashboard**: Comprehensive analytics and payment reporting
- **Notification System**: In-app notifications and SMS alerts
- **Review System**: Rate and review completed services
- **Mobile App**: Flutter devotee app for home, bookings, wallet, and support

## Tech Stack

- **Backend**: Django 4.2+, Python 3.11+
- **Database**: PostgreSQL (production) / SQLite (development)
- **Payments**: Razorpay integration
- **SMS**: Twilio integration
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Mobile**: Flutter (web, iOS, Android)
- **Deployment**: Gunicorn, Nginx, systemd

## Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sivaaSport/purohitconnect.git
   cd purohitconnect
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver 0.0.0.0:8001
   ```

7. **Run the Flutter app**
   ```bash
   cd mobile
   flutter run -d chrome --web-port=5173
   ```

### Production Deployment

See [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) for detailed instructions.

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection string
- `RAZORPAY_KEY_ID/SECRET`: Razorpay payment credentials
- `TWILIO_*`: SMS service credentials (optional)
- Security settings for production

### Key Settings

- **DEBUG**: Set to `False` in production
- **ALLOWED_HOSTS**: Configure for your domain
- **CSRF_TRUSTED_ORIGINS**: HTTPS origins for security
- **SECURE_SSL_REDIRECT**: Force HTTPS in production

## API Endpoints

### Authentication
- `POST /api/v1/auth/send-otp/` - Send OTP
- `POST /api/v1/auth/verify-otp/` - Verify OTP and login

### Bookings
- `GET /purohits/` - List purohits
- `POST /bookings/book/<package_id>/` - Create booking
- `GET /bookings/payment/<booking_id>/` - Payment options
- `POST /bookings/verify-payment/<booking_id>/` - Verify payment

### Wallet
- `GET /accounts/wallet/` - Wallet dashboard
- `POST /accounts/wallet/topup/` - Add money to wallet
- `GET /accounts/wallet/transactions/` - Transaction history

### Admin
- `GET /dashboard/admin/payments/` - Payment analytics
- `GET /dashboard/admin/support/` - Support tickets

## Testing

Run the test suite:

```bash
python manage.py test
```

Run specific app tests:

```bash
python manage.py test apps.accounts
python manage.py test apps.bookings
python manage.py test apps.api
```

## Project Structure

```
purohitconnect/
├── apps/                    # Django applications
│   ├── accounts/           # User authentication & wallet
│   ├── bookings/           # Booking management
│   ├── purohits/           # Purohit profiles
│   ├── dashboard/          # User/admin dashboards
│   ├── api/                # Mobile REST API
│   └── core/               # Shared functionality
├── mobile/                 # Flutter devotee app
├── config/                 # Django settings
├── static/                 # Static assets
├── templates/              # HTML templates
├── docs/                   # Documentation
├── .env.example           # Environment template
└── requirements.txt       # Python dependencies
```

## Documentation

- [Production Deployment Guide](docs/PRODUCTION_DEPLOYMENT.md) - Complete deployment instructions
- [Development Roadmap](docs/DEVELOPMENT_ROADMAP.md) - Complete feature roadmap and priorities
- [Reschedule Logic](docs/RESCHEDULE_LOGIC.md) - Booking reschedule implementation details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in `docs/`
- Contact the development team

## Security

If you discover security vulnerabilities, please email security@purohitconnect.com instead of creating public issues.

## Roadmap

- [x] Core booking and payment system
- [x] Wallet and Razorpay integration
- [x] Admin analytics dashboard
- [x] Mixed checkout support
- [x] Mobile app development
- [ ] Multi-language support
- [ ] Advanced reporting features
