# Frontend Application

<cite>
**Referenced Files in This Document**
- [apps/web/src/app/layout.tsx](file://apps/web/src/app/layout.tsx)
- [apps/web/src/components/providers.tsx](file://apps/web/src/components/providers.tsx)
- [apps/web/src/middleware.ts](file://apps/web/src/middleware.ts)
- [apps/web/src/app/(auth)/login/page.tsx](file://apps/web/src/app/(auth)/login/page.tsx)
- [apps/web/src/components/auth-guard.tsx](file://apps/web/src/components/auth-guard.tsx)
- [apps/web/src/store/auth.ts](file://apps/web/src/store/auth.ts)
- [apps/web/src/lib/api-client.ts](file://apps/web/src/lib/api-client.ts)
- [apps/web/src/app/(dashboard)/layout.tsx](file://apps/web/src/app/(dashboard)/layout.tsx)
- [apps/web/src/components/layout/sidebar.tsx](file://apps/web/src/components/layout/sidebar.tsx)
- [apps/web/src/components/kpi-card.tsx](file://apps/web/src/components/kpi-card.tsx)
- [apps/web/src/components/features/conversation-timeline.tsx](file://apps/web/src/components/features/conversation-timeline.tsx)
- [apps/web/src/components/features/ai-insights-panel.tsx](file://apps/web/src/components/features/ai-insights-panel.tsx)
- [apps/web/src/components/features/transcript-viewer.tsx](file://apps/web/src/components/features/transcript-viewer.tsx)
- [apps/web/package.json](file://apps/web/package.json)
- [apps/web/next.config.ts](file://apps/web/next.config.ts)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document describes the Xsamaa AI Pipeline web interface built with Next.js 16 using the App Router. It covers the application’s architecture, component hierarchy, state management with Zustand, dashboard layout and sidebar navigation, responsive design with Tailwind CSS and shadcn/ui, authentication flow and protected routes, role-based UI adaptation, and key UI components such as KPI cards, conversation timeline visualization, AI insights panel, and transcript viewer. It also documents the API integration layer, data-fetching strategies, and error handling patterns, along with guidelines for extending the UI while maintaining design consistency.

## Project Structure
The frontend is organized as a Next.js app under apps/web. The App Router separates public and protected areas using route groups. Authentication is handled client-side with a dedicated guard and Zustand store persisted in localStorage. Global providers configure React Query and UI tooltips. The dashboard layout composes a sidebar and main content area, with pages grouped under a protected dashboard route group.

```mermaid
graph TB
A["Root Layout<br/>(app/layout.tsx)"] --> B["Providers<br/>(components/providers.tsx)"]
B --> C["App Shell<br/>(app/(dashboard)/layout.tsx)"]
C --> D["Sidebar<br/>(components/layout/sidebar.tsx)"]
C --> E["Main Content Area"]
E --> F["Protected Pages<br/>(e.g., /brand, /stores)"]
E --> G["Public Pages<br/>(/login)"]
G --> H["Login Page<br/>(app/(auth)/login/page.tsx)"]
H --> I["Auth Guard<br/>(components/auth-guard.tsx)"]
I --> J["Zustand Auth Store<br/>(store/auth.ts)"]
J --> K["Local Storage"]
E --> L["Feature Components<br/>(kpi-card, timeline, insights, transcript)"]
L --> M["Shared Types<br/>(@samaa/shared)"]
E --> N["API Client<br/>(lib/api-client.ts)"]
```

**Diagram sources**
- [apps/web/src/app/layout.tsx:1-37](file://apps/web/src/app/layout.tsx#L1-L37)
- [apps/web/src/components/providers.tsx:1-26](file://apps/web/src/components/providers.tsx#L1-L26)
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)
- [apps/web/src/components/layout/sidebar.tsx:1-143](file://apps/web/src/components/layout/sidebar.tsx#L1-L143)
- [apps/web/src/app/(auth)/login/page.tsx:1-91](file://apps/web/src/app/(auth)/login/page.tsx#L1-L91)
- [apps/web/src/components/auth-guard.tsx:1-40](file://apps/web/src/components/auth-guard.tsx#L1-L40)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)

**Section sources**
- [apps/web/src/app/layout.tsx:1-37](file://apps/web/src/app/layout.tsx#L1-L37)
- [apps/web/src/components/providers.tsx:1-26](file://apps/web/src/components/providers.tsx#L1-L26)
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)
- [apps/web/src/middleware.ts:1-32](file://apps/web/src/middleware.ts#L1-L32)

## Core Components
- Providers: Wraps the app with React Query and Tooltip providers to enable caching, retries, and global tooltip behavior.
- AuthGuard: Enforces client-side route protection and redirects based on authentication state and pathname.
- Auth Store (Zustand): Manages user session state, persistence, and hydration from localStorage.
- API Client: Centralized HTTP client with automatic token injection, refresh flow, and structured error handling.
- Dashboard Layout: Composes the sidebar and main content area for protected routes.
- Feature Components: Reusable UI building blocks for KPIs, timelines, AI insights, and transcripts.

**Section sources**
- [apps/web/src/components/providers.tsx:1-26](file://apps/web/src/components/providers.tsx#L1-L26)
- [apps/web/src/components/auth-guard.tsx:1-40](file://apps/web/src/components/auth-guard.tsx#L1-L40)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)

## Architecture Overview
The application follows a layered architecture:
- Presentation Layer: Next.js App Router pages and shared UI components.
- State Management: Zustand store for authentication state with localStorage persistence.
- Data Access: Custom API client encapsulating HTTP requests, token refresh, and error normalization.
- UI Composition: Tailwind CSS and shadcn/ui primitives for consistent styling and responsive behavior.
- Routing and Protection: Route groups for protected/public areas, middleware allowing public paths, and client-side AuthGuard.

```mermaid
graph TB
subgraph "Presentation"
P1["Pages<br/>(login, dashboard)"]
P2["UI Components<br/>(cards, timeline, insights, transcript)"]
end
subgraph "State"
S1["Zustand Auth Store"]
S2["React Query Cache"]
end
subgraph "Services"
C1["API Client"]
C2["Middleware"]
end
P1 --> S1
P2 --> S1
P1 --> C1
P2 --> C1
P1 --> S2
P2 --> S2
C2 --> P1
C2 --> P2
```

**Diagram sources**
- [apps/web/src/app/(auth)/login/page.tsx:1-91](file://apps/web/src/app/(auth)/login/page.tsx#L1-L91)
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/components/providers.tsx:1-26](file://apps/web/src/components/providers.tsx#L1-L26)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [apps/web/src/middleware.ts:1-32](file://apps/web/src/middleware.ts#L1-L32)

## Detailed Component Analysis

### Authentication Flow and Protected Routes
The authentication system combines server-side middleware and client-side guards:
- Middleware allows public paths and static assets, deferring auth checks to the client.
- AuthGuard hydrates the store on mount, enforces redirects for unauthenticated users, and prevents access to login when already authenticated.
- The login page submits credentials via the API client, persists tokens and user data, and navigates to the home dashboard.

```mermaid
sequenceDiagram
participant U as "User"
participant MW as "Middleware"
participant AG as "AuthGuard"
participant LS as "LocalStorage"
participant ST as "Auth Store (Zustand)"
participant API as "API Client"
participant PG as "Protected Page"
U->>MW : Navigate to protected route
MW-->>U : Allow (public/static/API excluded)
U->>AG : Enter protected layout
AG->>ST : hydrate()
ST->>LS : Read user/token
LS-->>ST : Hydrated state
AG->>AG : Redirect if unauthenticated
U->>PG : Access allowed
U->>API : Submit login form
API-->>U : LoginResponse
U->>ST : login(LoginResponse)
ST->>LS : Persist tokens and user
U->>PG : Navigate to "/"
```

**Diagram sources**
- [apps/web/src/middleware.ts:1-32](file://apps/web/src/middleware.ts#L1-L32)
- [apps/web/src/components/auth-guard.tsx:1-40](file://apps/web/src/components/auth-guard.tsx#L1-L40)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [apps/web/src/app/(auth)/login/page.tsx:1-91](file://apps/web/src/app/(auth)/login/page.tsx#L1-L91)

**Section sources**
- [apps/web/src/middleware.ts:1-32](file://apps/web/src/middleware.ts#L1-L32)
- [apps/web/src/components/auth-guard.tsx:1-40](file://apps/web/src/components/auth-guard.tsx#L1-L40)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [apps/web/src/app/(auth)/login/page.tsx:1-91](file://apps/web/src/app/(auth)/login/page.tsx#L1-L91)

### Dashboard Layout and Sidebar Navigation
The dashboard layout composes the sidebar and main content area. The sidebar renders role-filtered navigation items, highlights the active route, and supports logout by clearing the auth store and redirecting to login.

```mermaid
flowchart TD
Start(["Render Dashboard Layout"]) --> LoadAuth["Load Auth State"]
LoadAuth --> RenderSidebar["Render Sidebar"]
RenderSidebar --> FilterNav["Filter Items by Role"]
FilterNav --> ActiveCheck{"Active Path?"}
ActiveCheck --> |Yes| Highlight["Highlight Active Item"]
ActiveCheck --> |No| Idle["No Highlight"]
RenderSidebar --> UserSection["Show User Info"]
UserSection --> Logout["Logout Handler"]
Logout --> ClearStore["Clear LocalStorage"]
ClearStore --> Redirect["Redirect to /login"]
RenderSidebar --> End(["Ready"])
```

**Diagram sources**
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)
- [apps/web/src/components/layout/sidebar.tsx:1-143](file://apps/web/src/components/layout/sidebar.tsx#L1-L143)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)

**Section sources**
- [apps/web/src/app/(dashboard)/layout.tsx:1-22](file://apps/web/src/app/(dashboard)/layout.tsx#L1-L22)
- [apps/web/src/components/layout/sidebar.tsx:1-143](file://apps/web/src/components/layout/sidebar.tsx#L1-L143)

### KPI Cards
KPI cards present metrics with optional trend indicators and icons. They accept props for title, value, description, icon, and trend data, rendering a consistent card layout using shadcn/ui primitives.

```mermaid
classDiagram
class KPICard {
+string title
+string|number value
+string description
+LucideIcon icon
+object trend
+boolean trend.isPositive
+number trend.value
}
```

**Diagram sources**
- [apps/web/src/components/kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)

**Section sources**
- [apps/web/src/components/kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)

### Conversation Timeline Visualization
The timeline component visualizes detected conversations as colored bars along a duration axis, with tooltips for timing and outcomes, and click handlers to focus on specific conversations.

```mermaid
flowchart TD
Init(["Receive Props"]) --> CheckEmpty{"Has Conversations?"}
CheckEmpty --> |No| NullReturn["Return null"]
CheckEmpty --> |Yes| CalcTotal["Compute Total Duration"]
CalcTotal --> LoopConv["Map Conversations"]
LoopConv --> ComputePos["Compute Left (%)"]
ComputePos --> ComputeWidth["Compute Width (%)"]
ComputeWidth --> OutcomeColor["Resolve Outcome Color"]
OutcomeColor --> Tooltip["Attach Tooltip"]
Tooltip --> ClickHandler["Attach Click Handler"]
ClickHandler --> Render["Render Bar"]
Render --> End(["Done"])
```

**Diagram sources**
- [apps/web/src/components/features/conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)

**Section sources**
- [apps/web/src/components/features/conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)

### AI Insights Panel
The AI insights panel displays structured analysis per conversation, including intent, outcome, budget, products, objections, competitors, closing attempt, summary, coaching notes, and score breakdowns. It supports click-to-focus and confidence badges.

```mermaid
classDiagram
class AIInsightsPanel {
+Conversation[] conversations
+Map~string, ConversationAnalysis~ analyses
+string activeConversationId
+onConversationClick(conversation)
}
```

**Diagram sources**
- [apps/web/src/components/features/ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)

**Section sources**
- [apps/web/src/components/features/ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)

### Transcript Viewer
The transcript viewer renders speaker-labeled segments with timestamps, groups segments by active conversation, and supports highlighting and click events to navigate between segments and conversations.

```mermaid
flowchart TD
Start(["Receive Segments"]) --> HasConvs{"Has Conversations?"}
HasConvs --> |No| MapNoConv["Map without grouping"]
HasConvs --> |Yes| Group["Group by Conversation Range"]
MapNoConv --> RenderList["Render List"]
Group --> RenderList
RenderList --> ClickSeg["On Segment Click"]
RenderList --> Highlight["Highlight Active Conversation"]
ClickSeg --> End(["Done"])
Highlight --> End
```

**Diagram sources**
- [apps/web/src/components/features/transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)

**Section sources**
- [apps/web/src/components/features/transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)

### API Integration Layer
The API client centralizes HTTP requests:
- Automatically injects Authorization header when a token exists.
- Handles 401 Unauthorized by attempting a token refresh using the refresh token.
- Normalizes errors into a structured ApiError with status and detail.
- Supports GET, POST, PUT, DELETE with JSON or FormData bodies.
- Treats 204 No Content as undefined return.

```mermaid
flowchart TD
Call(["api.get/post/put/delete"]) --> BuildHeaders["Build Headers"]
BuildHeaders --> SendReq["fetch(endpoint)"]
SendReq --> Status{"HTTP Status"}
Status --> |401 & Retry| Refresh["Refresh Token"]
Refresh --> Retry["Retry Request"]
Status --> |204| ReturnUndef["Return undefined"]
Status --> |2xx| ParseJSON["Parse JSON"]
Status --> |Other| ThrowErr["Throw ApiError"]
Retry --> Status
ParseJSON --> Done(["Return Data"])
ThrowErr --> Done
ReturnUndef --> Done
```

**Diagram sources**
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)

**Section sources**
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)

## Dependency Analysis
External dependencies relevant to UI and state include:
- next, react, react-dom for framework runtime
- @tanstack/react-query for caching and data fetching
- zustand for lightweight state management
- lucide-react for icons
- tailwind-merge, clsx, class-variance-authority for styling utilities
- recharts for charts (as per package.json)
- @samaa/shared for shared types and constants

```mermaid
graph LR
WebPkg["apps/web/package.json"] --> Next["next"]
WebPkg --> React["react / react-dom"]
WebPkg --> Query["@tanstack/react-query"]
WebPkg --> Zustand["zustand"]
WebPkg --> Icons["lucide-react"]
WebPkg --> Tailwind["tailwind-* utilities"]
WebPkg --> Shared["@samaa/shared"]
WebPkg --> Charts["recharts"]
```

**Diagram sources**
- [apps/web/package.json:1-38](file://apps/web/package.json#L1-L38)

**Section sources**
- [apps/web/package.json:1-38](file://apps/web/package.json#L1-L38)

## Performance Considerations
- React Query defaults: Queries have a short stale time and limited retries to balance freshness and resilience.
- Memoization: Transcript viewer uses memoization to avoid recomputation when conversations change but segments remain the same.
- Conditional rendering: Components return early when data is unavailable to prevent unnecessary work.
- Token refresh: The API client avoids infinite retry loops by disabling retries after a refresh attempt.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:
- Authentication loop or redirect to login:
  - Verify middleware allows public paths and static assets.
  - Ensure AuthGuard hydrates the store and redirects appropriately.
  - Confirm localStorage contains tokens and user data after login.
- 401 Unauthorized errors:
  - The API client attempts a token refresh automatically; if it fails, it clears auth state and redirects to login.
  - Check refresh token presence and backend refresh endpoint availability.
- UI not reflecting role-based navigation:
  - Confirm user role is persisted and the sidebar filters items based on roles.
- Empty or missing data in features:
  - Validate that conversations and analyses maps are populated before rendering.
  - Ensure transcript segments align with conversation time ranges.

**Section sources**
- [apps/web/src/middleware.ts:1-32](file://apps/web/src/middleware.ts#L1-L32)
- [apps/web/src/components/auth-guard.tsx:1-40](file://apps/web/src/components/auth-guard.tsx#L1-L40)
- [apps/web/src/store/auth.ts:1-49](file://apps/web/src/store/auth.ts#L1-L49)
- [apps/web/src/lib/api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [apps/web/src/components/layout/sidebar.tsx:1-143](file://apps/web/src/components/layout/sidebar.tsx#L1-L143)

## Conclusion
The Xsamaa AI Pipeline web interface leverages Next.js 16 App Router, Zustand for authentication state, and a custom API client to deliver a responsive, role-aware dashboard. The modular UI components, consistent styling with Tailwind and shadcn/ui, and robust data-fetching patterns enable scalable development and maintainable design.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Extending the UI with New Components
- Follow the existing component pattern: use shadcn/ui primitives, keep props minimal and typed, and leverage Tailwind utilities for styling.
- For new feature components, mirror the composition seen in timeline, insights, and transcript viewer: accept data props, compute derived visuals, and expose callbacks for interactions.
- Maintain design consistency by using the established color tokens and spacing scales.

[No sources needed since this section provides general guidance]

### Styling and Responsive Design
- The project uses Tailwind CSS v4 and shadcn/ui components. Fonts are configured globally via the root layout.
- Responsive breakpoints and utilities are applied directly in component classes; ensure new components follow the same approach.

**Section sources**
- [apps/web/src/app/layout.tsx:1-37](file://apps/web/src/app/layout.tsx#L1-L37)
- [apps/web/next.config.ts:1-8](file://apps/web/next.config.ts#L1-L8)