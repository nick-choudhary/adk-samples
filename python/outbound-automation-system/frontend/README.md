# Outbound Automation System - Frontend

Modern React frontend application for managing automated outbound campaigns with multi-channel outreach (Email, SMS, Voice Calls).

## Features

- **Campaign Dashboard** - View and manage all campaigns with real-time stats
- **Campaign Creation Wizard** - Multi-step form for creating targeted campaigns
- **Lead Management** - Browse, filter, and sort leads with detailed information
- **Analytics Dashboard** - Track campaign performance with key metrics
- **Real-time Updates** - Automatic data refresh using React Query
- **Responsive Design** - Mobile-friendly UI with Tailwind CSS
- **Type Safety** - Full TypeScript coverage for better developer experience

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **React Router** - Client-side routing
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first styling
- **React Hook Form** - Form validation
- **Zod** - Schema validation
- **Lucide React** - Beautiful icons
- **date-fns** - Date formatting

## Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on port 8080 (see `../backend/`)

## Installation

1. **Install dependencies:**

```bash
npm install
```

2. **Configure environment:**

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
VITE_API_URL=http://localhost:8080
VITE_API_TIMEOUT=30000
VITE_AUTH_ENABLED=false
```

## Development

### Start development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000

### Other commands:

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Docker Development

### Build and run with Docker:

```bash
# Build the development image
docker build -f Dockerfile.dev -t outbound-frontend-dev .

# Run the container
docker run -p 3000:3000 -v $(pwd):/app -v /app/node_modules outbound-frontend-dev
```

### Using docker-compose (from project root):

```bash
cd ..
docker-compose up frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # API client with React Query hooks
│   ├── components/
│   │   ├── CampaignCard.tsx   # Campaign summary card
│   │   ├── LeadTable.tsx      # Sortable lead table
│   │   └── StatsCard.tsx      # Metric display card
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main dashboard page
│   │   ├── CampaignDetails.tsx # Campaign detail view
│   │   └── CreateCampaign.tsx # Campaign creation wizard
│   ├── types/
│   │   └── index.ts           # TypeScript type definitions
│   ├── App.tsx                # Main app component with routing
│   ├── main.tsx               # Application entry point
│   └── index.css              # Global styles (Tailwind)
├── public/                     # Static assets
├── index.html                  # HTML template
├── package.json                # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
└── README.md                   # This file
```

## Key Components

### Dashboard (`src/pages/Dashboard.tsx`)

Main landing page showing:
- Aggregate statistics across all campaigns
- Campaign cards with key metrics
- Status filtering
- Quick actions (create, view, delete)

### Campaign Details (`src/pages/CampaignDetails.tsx`)

Detailed campaign view with:
- Real-time performance metrics
- Lead list with sorting/filtering
- Campaign management actions (pause/resume)
- Export functionality

### Create Campaign (`src/pages/CreateCampaign.tsx`)

Multi-step wizard for campaign creation:
1. **Campaign Info** - Name, geography, target count
2. **Target Audience** - Industries, titles, company size
3. **Lead Sources** - Data source selection, scoring threshold
4. **Review & Launch** - Summary and submission

## API Integration

The frontend communicates with the backend API using axios and React Query:

```typescript
// Example: Fetching campaigns
import { useCampaigns } from './api/client';

function MyComponent() {
  const { data: campaigns, isLoading } = useCampaigns();
  // ...
}
```

### Available Hooks:

- `useCampaigns(status?)` - List campaigns
- `useCampaign(id)` - Get campaign details
- `useCampaignStats(id)` - Get campaign statistics
- `useLeads(campaignId)` - Get campaign leads
- `useCreateCampaign()` - Create new campaign
- `useDeleteCampaign()` - Delete campaign
- `useExtractLeads()` - Start lead extraction
- `useStartOutreach()` - Start outreach campaign
- `usePauseOutreach()` - Pause campaign
- `useResumeOutreach()` - Resume campaign
- `useJobStatus(jobId)` - Poll job status

## Styling

This project uses Tailwind CSS for styling. Key customizations in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Custom blue palette
        500: '#0ea5e9',
        600: '#0284c7',
        700: '#0369a1',
      },
    },
  },
}
```

## Type Safety

All API responses and component props are fully typed. See `src/types/index.ts` for definitions:

- `Campaign` - Campaign data structure
- `Lead` - Lead data structure
- `CampaignStats` - Performance metrics
- `JobResponse` - Async job responses
- And more...

## State Management

- **React Query** handles server state (campaigns, leads, stats)
- **React Hook Form** manages form state
- **React Router** manages routing state
- Local UI state uses React hooks (useState, useReducer)

## Performance Optimizations

- Code splitting with React.lazy (ready for expansion)
- React Query caching and automatic refetching
- Debounced search inputs (ready to add)
- Virtualized lists for large datasets (can be added)
- Image lazy loading
- Bundle size optimization with Vite

## Browser Support

- Chrome/Edge (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)

## Troubleshooting

### Port already in use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
npm run dev -- --port 3001
```

### Module not found errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API connection issues

Check that:
1. Backend is running on port 8080
2. `.env` has correct `VITE_API_URL`
3. CORS is enabled in backend
4. Network/firewall allows connections

### Type errors

```bash
# Regenerate type definitions if backend schema changed
npm run type-check
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8080` |
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` |
| `VITE_AUTH_ENABLED` | Enable authentication | `false` |

## Production Build

```bash
# Build for production
npm run build

# Output will be in dist/
# Deploy dist/ to your hosting service (Vercel, Netlify, etc.)
```

## Testing (Coming Soon)

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run linting and type checking
4. Submit a pull request

## License

Apache License 2.0

## Support

For issues or questions:
- File an issue on GitHub
- Check existing documentation
- Review API docs at http://localhost:8080/docs

---

Built with React, TypeScript, and Tailwind CSS
