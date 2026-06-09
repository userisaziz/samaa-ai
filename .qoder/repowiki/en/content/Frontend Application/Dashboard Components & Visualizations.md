# Dashboard Components & Visualizations

<cite>
**Referenced Files in This Document**
- [kpi-card.tsx](file://apps/web/src/components/kpi-card.tsx)
- [conversation-timeline.tsx](file://apps/web/src/components/features/conversation-timeline.tsx)
- [ai-insights-panel.tsx](file://apps/web/src/components/features/ai-insights-panel.tsx)
- [transcript-viewer.tsx](file://apps/web/src/components/features/transcript-viewer.tsx)
- [conversation-drawer.tsx](file://apps/web/src/components/features/conversation-drawer.tsx)
- [api-types.ts](file://packages/shared/src/api-types.ts)
- [constants.ts](file://packages/shared/src/constants.ts)
- [api-client.ts](file://apps/web/src/lib/api-client.ts)
- [recordings-page.tsx](file://apps/web/src/app/(dashboard)/recordings/page.tsx)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx)
- [card.tsx](file://apps/web/src/components/ui/card.tsx)
- [tooltip.tsx](file://apps/web/src/components/ui/tooltip.tsx)
- [sheet.tsx](file://apps/web/src/components/ui/sheet.tsx)
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
This document provides comprehensive documentation for the specialized dashboard components and data visualization features used in the audio conversation analytics dashboard. It covers:
- KPI card component with metric display, trend indicators, and interactive elements
- Conversation timeline visualization with timeline rendering, event markers, and playback controls
- AI insights panel with insight cards, filtering capabilities, and export functionality
- Transcript viewer with word highlighting, speaker identification, and annotation features
- Conversation drawer with expandable content, navigation controls, and contextual actions

It also documents component props, event handlers, state management patterns, integration examples, data binding, user interaction handling, and performance optimization strategies for large datasets and real-time updates.

## Project Structure
The dashboard components are organized under the Next.js web application’s components directory, with feature-specific components grouped under a dedicated features folder. Shared data types and constants are defined in a separate package consumed by both the API server and the frontend.

```mermaid
graph TB
subgraph "Web App"
subgraph "Components"
KPI["KPI Card<br/>kpi-card.tsx"]
CT["Conversation Timeline<br/>features/conversation-timeline.tsx"]
AIP["AI Insights Panel<br/>features/ai-insights-panel.tsx"]
TV["Transcript Viewer<br/>features/transcript-viewer.tsx"]
CD["Conversation Drawer<br/>features/conversation-drawer.tsx"]
CardUI["Card UI<br/>ui/card.tsx"]
Tooltip["Tooltip UI<br/>ui/tooltip.tsx"]
Sheet["Sheet UI<br/>ui/sheet.tsx"]
end
subgraph "Pages"
RP["Recordings List<br/>app/(dashboard)/recordings/page.tsx"]
RDP["Recording Detail<br/>app/(dashboard)/recordings/[id]/page.tsx"]
end
end
subgraph "Shared Types"
AT["API Types<br/>packages/shared/src/api-types.ts"]
CTS["Constants<br/>packages/shared/src/constants.ts"]
end
subgraph "API Client"
AC["API Client<br/>apps/web/src/lib/api-client.ts"]
end
RP --> KPI
RP --> CT
RDP --> KPI
RDP --> CT
RDP --> AIP
RDP --> TV
RDP --> CD
CT --> Tooltip
AIP --> CardUI
CD --> Sheet
TV --> CardUI
RDP --> AC
AC --> AT
AT --> CTS
```

**Diagram sources**
- [kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)
- [conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)
- [ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)
- [transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)
- [conversation-drawer.tsx:1-193](file://apps/web/src/components/features/conversation-drawer.tsx#L1-L193)
- [card.tsx:1-104](file://apps/web/src/components/ui/card.tsx#L1-L104)
- [tooltip.tsx:1-67](file://apps/web/src/components/ui/tooltip.tsx#L1-L67)
- [sheet.tsx:1-139](file://apps/web/src/components/ui/sheet.tsx#L1-L139)
- [recordings-page.tsx](file://apps/web/src/app/(dashboard)/recordings/page.tsx#L1-L292)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L1-L258)
- [api-types.ts:1-228](file://packages/shared/src/api-types.ts#L1-L228)
- [constants.ts:1-40](file://packages/shared/src/constants.ts#L1-L40)
- [api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)

**Section sources**
- [recordings-page.tsx](file://apps/web/src/app/(dashboard)/recordings/page.tsx#L1-L292)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L1-L258)

## Core Components
This section summarizes the primary dashboard components and their responsibilities.

- KPI Card
  - Purpose: Display key metrics with optional trend indicators and icons.
  - Props: title, value, description, icon, trend.
  - Interactions: None; renders static metric display.
  - Typical usage: Summary cards on the recording detail page.

- Conversation Timeline
  - Purpose: Visualize conversation segments along a timeline with outcome coloring and tooltips.
  - Props: conversations, analyses (Map), recordingDuration, activeConversationId, onConversationClick.
  - Interactions: Click segment to toggle selection; hover for tooltip with timing and summary.
  - Rendering: Percentage-based positioning; outcome-driven color mapping.

- AI Insights Panel
  - Purpose: Present AI-generated insights per conversation with intent/outcome badges, product lists, objections, and score breakdowns.
  - Props: conversations, analyses (Map), onConversationClick, activeConversationId.
  - Interactions: Click card to open drawer with detailed view.
  - Rendering: Conditional sections for intent, outcome, budget, products, objections, competitors, closing attempt, summary, coaching notes, and scores.

- Transcript Viewer
  - Purpose: Render transcript segments with speaker labeling, timestamps, and optional conversation grouping.
  - Props: segments, conversations, activeConversationId, onSegmentClick.
  - Interactions: Click segment to highlight associated conversation; hover styles applied.
  - Rendering: Speaker color mapping; time formatting; grouped by conversation time range.

- Conversation Drawer
  - Purpose: Expandable panel showing detailed AI analysis and transcript for a selected conversation.
  - Props: conversation, open, onOpenChange.
  - Interactions: Opens/closes via Sheet; loads analysis and transcript via queries.
  - Rendering: Summary, outcome/intent badges, products/budget, objections, coaching notes, performance scores, and embedded TranscriptViewer.

**Section sources**
- [kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)
- [conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)
- [ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)
- [transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)
- [conversation-drawer.tsx:1-193](file://apps/web/src/components/features/conversation-drawer.tsx#L1-L193)

## Architecture Overview
The dashboard integrates React components with TanStack Query for data fetching and caching, a shared API client for HTTP requests, and UI primitives for consistent styling and interactions. The recording detail page orchestrates multiple components and manages state for active selections and drawer visibility.

```mermaid
sequenceDiagram
participant User as "User"
participant Page as "Recording Detail Page"
participant Timeline as "Conversation Timeline"
participant Insights as "AI Insights Panel"
participant Drawer as "Conversation Drawer"
participant API as "API Client"
User->>Page : Load page
Page->>API : Fetch recording, transcript, conversations, analyses
API-->>Page : Data
Page->>Timeline : Pass conversations, analyses, durations
Page->>Insights : Pass conversations, analyses
User->>Timeline : Click segment
Timeline-->>Page : onConversationClick(conversation)
Page->>Page : Set activeConversationId
User->>Insights : Click insight card
Insights-->>Page : onConversationClick(conversation)
Page->>Drawer : Open with selected conversation
Drawer->>API : Fetch analysis and transcript
API-->>Drawer : Data
Drawer-->>User : Render expanded details
```

**Diagram sources**
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L38-L257)
- [conversation-timeline.tsx:28-81](file://apps/web/src/components/features/conversation-timeline.tsx#L28-L81)
- [ai-insights-panel.tsx:37-202](file://apps/web/src/components/features/ai-insights-panel.tsx#L37-L202)
- [conversation-drawer.tsx:44-192](file://apps/web/src/components/features/conversation-drawer.tsx#L44-L192)
- [api-client.ts:39-114](file://apps/web/src/lib/api-client.ts#L39-L114)

## Detailed Component Analysis

### KPI Card Component
- Purpose: Lightweight metric display with optional description and trend indicator.
- Props:
  - title: string
  - value: string | number
  - description?: string
  - icon: LucideIcon
  - trend?: { value: number; isPositive: boolean }
- Behavior:
  - Renders a card header with title and icon.
  - Displays value and optional description.
  - Shows trend percentage with positive/negative styling.
- Integration:
  - Used on the recording detail page to show summary metrics.

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
- [kpi-card.tsx:4-13](file://apps/web/src/components/kpi-card.tsx#L4-L13)

**Section sources**
- [kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L162-L185)

### Conversation Timeline Visualization
- Purpose: Visualize detected conversation segments along the recording timeline.
- Props:
  - conversations: Conversation[]
  - analyses?: Map<string, ConversationAnalysis>
  - recordingDuration?: number | null
  - activeConversationId?: string | null
  - onConversationClick?: (conversation: Conversation) => void
- Behavior:
  - Calculates left (%) and width (%) for each segment based on normalized timestamps.
  - Applies outcome-based color mapping; highlights active segment.
  - Uses Tooltip for hover details (timing, summary, outcome).
- Interaction:
  - Click triggers onConversationClick callback to update active selection.

```mermaid
flowchart TD
Start(["Render Timeline"]) --> CheckEmpty{"Has conversations?"}
CheckEmpty --> |No| NullReturn["Return null"]
CheckEmpty --> |Yes| CalcTotal["Compute total duration"]
CalcTotal --> LoopConv["For each conversation"]
LoopConv --> ComputePos["Compute left (%) and width (%)"]
ComputePos --> GetAnalysis["Get analysis by ID"]
GetAnalysis --> ColorMap["Map outcome to color"]
ColorMap --> IsActive{"Is active?"}
IsActive --> |Yes| ApplyActive["Apply active ring styles"]
IsActive --> |No| ApplyInactive["Apply inactive opacity"]
ApplyActive --> Tooltip["Attach tooltip with details"]
ApplyInactive --> Tooltip
Tooltip --> NextConv{"More conversations?"}
NextConv --> |Yes| LoopConv
NextConv --> |No| Done(["Render"])
```

**Diagram sources**
- [conversation-timeline.tsx:28-81](file://apps/web/src/components/features/conversation-timeline.tsx#L28-L81)

**Section sources**
- [conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)
- [constants.ts:27-33](file://packages/shared/src/constants.ts#L27-L33)

### AI Insights Panel
- Purpose: Present AI analysis per conversation with intent/outcome, products, objections, and performance scores.
- Props:
  - conversations: Conversation[]
  - analyses: Map<string, ConversationAnalysis>
  - onConversationClick?: (conversation: Conversation) => void
  - activeConversationId?: string | null
- Behavior:
  - Iterates conversations and renders cards with analysis data.
  - Highlights active card; shows confidence badge and outcome/intent.
  - Conditionally renders budget, products, objections, competitors, closing attempt, summary, coaching notes, and score grid.
- Interaction:
  - Clicking a card invokes onConversationClick to open the drawer.

```mermaid
classDiagram
class AIInsightsPanel {
+Conversation[] conversations
+Map~string, ConversationAnalysis~ analyses
+string activeConversationId
+onConversationClick(conversation)
}
class ConversationAnalysis {
+string id
+string conversation_id
+string intent
+string[] products
+string budget
+string[] objections
+string[] competitors
+boolean closing_attempt
+Outcome outcome
+number confidence
+PerformanceScores scores
+string summary
+string coaching_notes
}
AIInsightsPanel --> ConversationAnalysis : "uses"
```

**Diagram sources**
- [ai-insights-panel.tsx:24-42](file://apps/web/src/components/features/ai-insights-panel.tsx#L24-L42)
- [api-types.ts:156-171](file://packages/shared/src/api-types.ts#L156-L171)

**Section sources**
- [ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)
- [api-types.ts:135-179](file://packages/shared/src/api-types.ts#L135-L179)

### Transcript Viewer
- Purpose: Render transcript segments with speaker identification, timestamps, and optional conversation association.
- Props:
  - segments: TranscriptSegment[]
  - conversations?: Conversation[]
  - activeConversationId?: string | null
  - onSegmentClick?: (segment: TranscriptSegment) => void
- Behavior:
  - Groups segments by conversation time range to compute conversationId.
  - Renders each segment with speaker label color, formatted timestamp, and text.
  - Highlights active segment when conversation matches activeConversationId.
- Interaction:
  - Clicking a segment invokes onSegmentClick; parent can set activeConversationId.

```mermaid
flowchart TD
Start(["Render Transcript"]) --> CheckSegs{"Segments empty?"}
CheckSegs --> |Yes| EmptyMsg["Show 'No transcript' message"]
CheckSegs --> |No| Group["Group segments by conversation"]
Group --> LoopSeg["For each segment"]
LoopSeg --> Highlight{"Match active conversation?"}
Highlight --> |Yes| ApplyActive["Apply active background"]
Highlight --> |No| ApplyDefault["Default styles"]
ApplyActive --> Click["Attach click handler"]
ApplyDefault --> Click
Click --> NextSeg{"More segments?"}
NextSeg --> |Yes| LoopSeg
NextSeg --> |No| Done(["Render"])
```

**Diagram sources**
- [transcript-viewer.tsx:33-88](file://apps/web/src/components/features/transcript-viewer.tsx#L33-L88)

**Section sources**
- [transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)
- [api-types.ts:135-143](file://packages/shared/src/api-types.ts#L135-L143)

### Conversation Drawer
- Purpose: Expandable panel displaying detailed AI analysis and transcript for a selected conversation.
- Props:
  - conversation: Conversation | null
  - open: boolean
  - onOpenChange: (open: boolean) => void
- Behavior:
  - Fetches analysis and transcript via TanStack Query when conversation is present.
  - Filters transcript segments to the selected conversation’s time window.
  - Renders summary, outcome/intent, products/budget, objections, coaching notes, and performance scores.
  - Embeds TranscriptViewer for the filtered segments.
- Interaction:
  - Controlled via Sheet; opens/closes based on open prop; passes onOpenChange up.

```mermaid
sequenceDiagram
participant Drawer as "ConversationDrawer"
participant Query as "TanStack Query"
participant API as "API Client"
participant TV as "TranscriptViewer"
Drawer->>Query : useQuery(conversation-analysis)
Query->>API : GET /conversations/{id}/analysis
API-->>Query : ConversationAnalysis
Query-->>Drawer : analysis
Drawer->>Query : useQuery(recording-transcript)
Query->>API : GET /recordings/{recording_id}/transcript
API-->>Query : TranscriptSegment[]
Query-->>Drawer : transcriptSegments
Drawer->>Drawer : Filter segments by conversation time range
Drawer->>TV : Render with filtered segments
```

**Diagram sources**
- [conversation-drawer.tsx:47-64](file://apps/web/src/components/features/conversation-drawer.tsx#L47-L64)
- [api-client.ts:39-114](file://apps/web/src/lib/api-client.ts#L39-L114)

**Section sources**
- [conversation-drawer.tsx:1-193](file://apps/web/src/components/features/conversation-drawer.tsx#L1-L193)
- [sheet.tsx:1-139](file://apps/web/src/components/ui/sheet.tsx#L1-L139)

## Dependency Analysis
The components rely on shared types and constants, UI primitives, and a centralized API client. The recording detail page coordinates data fetching and state for all components.

```mermaid
graph LR
RP["Recordings Page"] --> RDP["Recording Detail Page"]
RDP --> KPI["KPI Card"]
RDP --> CT["Conversation Timeline"]
RDP --> AIP["AI Insights Panel"]
RDP --> TV["Transcript Viewer"]
RDP --> CD["Conversation Drawer"]
CT --> Tooltip["Tooltip UI"]
AIP --> CardUI["Card UI"]
CD --> Sheet["Sheet UI"]
RDP --> AC["API Client"]
AC --> AT["API Types"]
AT --> CTS["Constants"]
```

**Diagram sources**
- [recordings-page.tsx](file://apps/web/src/app/(dashboard)/recordings/page.tsx#L1-L292)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L1-L258)
- [kpi-card.tsx:1-41](file://apps/web/src/components/kpi-card.tsx#L1-L41)
- [conversation-timeline.tsx:1-82](file://apps/web/src/components/features/conversation-timeline.tsx#L1-L82)
- [ai-insights-panel.tsx:1-203](file://apps/web/src/components/features/ai-insights-panel.tsx#L1-L203)
- [transcript-viewer.tsx:1-89](file://apps/web/src/components/features/transcript-viewer.tsx#L1-L89)
- [conversation-drawer.tsx:1-193](file://apps/web/src/components/features/conversation-drawer.tsx#L1-L193)
- [tooltip.tsx:1-67](file://apps/web/src/components/ui/tooltip.tsx#L1-L67)
- [card.tsx:1-104](file://apps/web/src/components/ui/card.tsx#L1-L104)
- [sheet.tsx:1-139](file://apps/web/src/components/ui/sheet.tsx#L1-L139)
- [api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [api-types.ts:1-228](file://packages/shared/src/api-types.ts#L1-L228)
- [constants.ts:1-40](file://packages/shared/src/constants.ts#L1-L40)

**Section sources**
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L1-L258)
- [api-client.ts:1-114](file://apps/web/src/lib/api-client.ts#L1-L114)
- [api-types.ts:1-228](file://packages/shared/src/api-types.ts#L1-L228)
- [constants.ts:1-40](file://packages/shared/src/constants.ts#L1-L40)

## Performance Considerations
- Efficient rendering
  - Conversation Timeline: Renders a fixed number of DOM nodes proportional to conversation count; percentage-based layout minimizes reflows.
  - AI Insights Panel: Iterates conversations and conditionally renders sections; keep analyses Map lookup O(1).
  - Transcript Viewer: Memoizes grouped segments to avoid recomputation when conversations change; renders only visible segments.
  - Conversation Drawer: Lazy-loads analysis and transcript; filters segments client-side within the conversation’s time window.
- Real-time updates
  - Recording list page uses periodic refetch while any recording is processing to reflect progress without manual refresh.
  - Recording detail page uses targeted refetch intervals for recording status and summary to balance freshness and cost.
- Data fetching
  - TanStack Query caches responses by query keys; use staleTime and gcTime appropriately to minimize redundant network calls.
  - Parallelize independent queries (e.g., transcript and analyses) where possible; batch dependent queries to reduce round trips.
- UI responsiveness
  - Use virtualized lists for very large transcripts to limit DOM nodes.
  - Debounce user interactions (e.g., search/filter) to avoid excessive re-renders.
- Network reliability
  - API client handles 401 with automatic token refresh and redirects to login; ensure proper error boundaries around queries.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- Authentication errors
  - Symptom: Requests fail with 401 Unauthorized.
  - Resolution: API client automatically attempts token refresh; if unsuccessful, clears auth state and navigates to login. Verify stored tokens and refresh token endpoint availability.
- Missing or delayed data
  - Symptom: Analyses or transcripts appear empty initially.
  - Resolution: Ensure recording status is COMPLETED before requesting analyses; confirm query keys include conversation IDs; verify backend processing completion.
- Drawer not opening
  - Symptom: Clicking an insight does not open the drawer.
  - Resolution: Confirm onConversationClick is passed to AI Insights Panel and that it sets the drawer’s conversation and open state.
- Timeline misalignment
  - Symptom: Segments overlap or do not span the full duration.
  - Resolution: Ensure recordingDuration is provided when conversations lack end_time; validate that start_time and end_time are normalized consistently.

**Section sources**
- [api-client.ts:39-114](file://apps/web/src/lib/api-client.ts#L39-L114)
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L78-L98)
- [conversation-timeline.tsx:37-52](file://apps/web/src/components/features/conversation-timeline.tsx#L37-L52)

## Conclusion
The dashboard components provide a cohesive, data-driven interface for analyzing audio conversations. They leverage shared types, a robust API client, and UI primitives to deliver responsive visualizations and actionable insights. By following the integration patterns and performance recommendations outlined here, teams can maintain scalability and usability as datasets grow and real-time updates become more frequent.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### Component Prop Reference
- KPI Card
  - title: string
  - value: string | number
  - description?: string
  - icon: LucideIcon
  - trend?: { value: number; isPositive: boolean }

- Conversation Timeline
  - conversations: Conversation[]
  - analyses?: Map<string, ConversationAnalysis>
  - recordingDuration?: number | null
  - activeConversationId?: string | null
  - onConversationClick?: (conversation: Conversation) => void

- AI Insights Panel
  - conversations: Conversation[]
  - analyses: Map<string, ConversationAnalysis>
  - onConversationClick?: (conversation: Conversation) => void
  - activeConversationId?: string | null

- Transcript Viewer
  - segments: TranscriptSegment[]
  - conversations?: Conversation[]
  - activeConversationId?: string | null
  - onSegmentClick?: (segment: TranscriptSegment) => void

- Conversation Drawer
  - conversation: Conversation | null
  - open: boolean
  - onOpenChange: (open: boolean) => void

**Section sources**
- [kpi-card.tsx:4-13](file://apps/web/src/components/kpi-card.tsx#L4-L13)
- [conversation-timeline.tsx:13-19](file://apps/web/src/components/features/conversation-timeline.tsx#L13-L19)
- [ai-insights-panel.tsx:24-29](file://apps/web/src/components/features/ai-insights-panel.tsx#L24-L29)
- [transcript-viewer.tsx:25-31](file://apps/web/src/components/features/transcript-viewer.tsx#L25-L31)
- [conversation-drawer.tsx:32-36](file://apps/web/src/components/features/conversation-drawer.tsx#L32-L36)

### Example Integrations
- Recording Detail Page
  - Fetches recording, transcript, conversations, and analyses.
  - Passes props to KPI Card, Conversation Timeline, AI Insights Panel, Transcript Viewer, and Conversation Drawer.
  - Manages activeConversationId and drawer state.

**Section sources**
- [recording-detail-page.tsx](file://apps/web/src/app/(dashboard)/recordings/[id]/page.tsx#L46-L124)