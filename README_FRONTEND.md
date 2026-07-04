# DealBrief AI - Frontend

DealBrief AI is an AI-powered sales meeting preparation platform. This frontend generates customized sales briefs, talking points, suggested questions, and engagement tracking.

## Features

✅ Customer Selection  
✅ Meeting Context Configuration (Type, Product, Deliverable)  
✅ AI-Generated Sales Briefs  
✅ Talking Points & Suggested Questions  
✅ Engagement Log Tracking  
✅ Responsive Design

## Project Structure

```
src/
├── App.jsx              # Main application component
├── App.css              # Application styles
├── main.jsx             # React entry point
├── index.css            # Global styles
└── components/
    ├── MeetingForm.jsx  # Meeting context form
    ├── ResultPanel.jsx  # AI brief results display
    ├── EngagementLog.jsx # Engagement log history
    └── index.js         # Component exports
```

## Getting Started

### Installation

```bash
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Create a production build:

```bash
npm run build
```

### Preview

Preview the production build:

```bash
npm run preview
```

## Technology Stack

- **Frontend**: React 19.2.7
- **Build Tool**: Vite 8.1.0
- **Styling**: CSS (Grid, Flexbox)
- **Language**: JavaScript (JSX)

## API Integration

The current implementation uses mock data for demonstration. To integrate with a backend:

1. Update the `handleGenerate` function in `App.jsx`
2. Replace the mock data generation with an actual API call:

```javascript
const response = await fetch("/api/generate-brief", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    customer,
    meetingType,
    product,
    deliverable,
    notes,
  }),
});
const brief = await response.json();
```

## Environment Variables

Create a `.env` file in the root directory (see `.env.example`):

```
VITE_API_URL=http://localhost:3000/api
```

## Component API

### MeetingForm

Displays the form for selecting meeting context.

Props:

- `customer`, `meetingType`, `product`, `deliverable`, `notes`: Form state
- Setters for each state
- `customers`, `meetingTypes`, `products`, `deliverables`: Dropdown options
- `onGenerate`: Handler for generate button
- `loading`: Loading state

### ResultPanel

Displays the AI-generated brief results.

Props:

- `result`: Brief data object with `overview`, `talkingPoints`, `questions`, `nextSteps`, `risk`

### EngagementLog

Displays the engagement history.

Props:

- `log`: Array of generated briefs

## Future Enhancements

- User authentication & admin dashboard
- File upload (PDF, CSV) support
- Real-time Salesforce data integration
- Export briefs to PDF
- Collaboration features
- Advanced analytics

## License

MIT
