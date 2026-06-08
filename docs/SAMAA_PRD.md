SAMAA — Product Requirements Document	Confidential  |  v1.0

|<p>**SAMAA**</p><p>Sales Audio Management & AI Analysis</p><p>*Product Requirements Document*</p>|
| :-: |

|**Version**|1\.0|
| :- | :- |
|**Status**|Draft|
|**Classification**|Confidential|


# **Executive Summary**

SAMAA (Sales Audio Management & AI Analysis) is an enterprise intelligence platform designed for retail organizations. It transforms raw, unstructured audio recordings from retail store floors into structured, actionable business intelligence.

The platform addresses a critical gap: retail managers currently have no visibility into what actually happens in customer conversations. SAMAA fills this gap by automatically processing hours of store audio, extracting insights from every customer interaction, and surfacing them in intuitive dashboards at every level of the organization.

### **Strategic Questions SAMAA Answers**

|🎯  What are customers asking for?|📈  Which stores perform best?|
| :- | :- |
|❓  Why are sales being lost?|🔊  What objections are increasing?|
|👤  Who needs coaching?|🛍️  Which products generate interest?|


# **Product Overview**

## **Product Hierarchy**

|**🏢  BRAND**|
| :- |
|`    `**└──  🏪  STORE**|
|`         `**└──  👤  SALESPERSON**|
|`              `**└──  🎙️  AUDIO RECORDING**|
|`                   `**└──  💬  CONVERSATIONS**|
|`                        `**└──  🤖  AI ANALYSIS**|

## **Target Users**

|**Role**|**Primary Need**|**Key Deliverable**|
| :- | :- | :- |
|**Brand Admin**|Cross-store performance visibility|Brand-level dashboard with store rankings|
|**Store Manager**|Identify coaching opportunities|Store dashboard with salesperson scores|
|**Sales Manager**|Individual salesperson performance|Salesperson profiles with skill analysis|
|**Salesperson**|Personal performance feedback|Coaching recommendations per conversation|



|**MODULE 1 — AI PLATFORM**|
| :- |

|Objective: Convert 8-hour retail audio recordings into structured business intelligence through a multi-stage AI pipeline.|
| :- |

## **AI Pipeline Overview**

||**1. Audio Ingestion**||
| :- | :-: | :- |
||**2. Preprocessing**||
||**3. Speech-to-Text (ASR)**||
||**4. Speaker Diarization**||
||**5. Conversation Segmentation**||
||**6. Conversation Analysis**||
||**7. Salesperson Scoring**||
||**8. Aggregation & Reporting**||

## **AI-01  Audio Ingestion**
**Input Formats**

|**.WAV**|**.MP3**|**.M4A**|
| :-: | :-: | :-: |

**Requirements**

- Validate file format and MIME type
- Validate audio duration (minimum 1 minute, maximum 12 hours)
- Store metadata to the recordings table
- Generate an async processing job in the queue
- Return a recordingId and status: uploaded

## **AI-02  Audio Preprocessing**
**Goal**

Standardize raw audio to a consistent format before feeding into AI models.

**Processing Tasks**

|**Task**|**Specification**|
| :- | :- |
|**Convert to mono**|Single channel audio|
|**Normalize volume**|Consistent amplitude levels|
|**Resample**|16kHz sample rate|
|**Silence detection**|Flag gaps longer than 30 seconds|
|**Corrupt segment removal**|Skip unreadable audio blocks|

## **AI-03  Speech-to-Text**

|**Model**|NVIDIA Parakeet 1.1B RNNT Multilingual|
| :- | :- |
|**Languages**|25 languages supported|
|**Output Format**|Timestamped word-level transcript JSON|
|**Quality Target**|> 90% accuracy on test samples|

**Output Schema**

|[ { "start": 12.5, "end": 15.2, "speaker": "A", "text": "Welcome, sir. How can I help you today?" } ]|
| :- |

## **AI-04  Speaker Diarization**
**Goal**

Separate and label individual speakers throughout the audio recording to distinguish the salesperson from the customer.

**Model**

NVIDIA NeMo Speaker Diarization

**Requirements**

- Detect the number of unique speakers
- Assign speaker labels (Speaker A, Speaker B, etc.)
- Merge speaker labels with transcript timestamps
- Handle overlapping speech gracefully

## **AI-05  Conversation Segmentation**
**Goal**

Convert a single 8-hour store recording into discrete, individual customer conversations.

**Segmentation Rules**

|**Signal**|**Rule**|
| :- | :- |
|**Silence Gap**|Gap > 30 seconds marks a conversation boundary|
|**Greeting Detection**|Salesperson greeting indicates a new conversation start|
|**Departure Detection**|Farewell phrases indicate a conversation end|
|**New Speaker Entry**|New speaker appearing after silence|

## **AI-06  Conversation Analysis**

|**Model**|Llama 3.3 70B|
| :- | :- |
|**Input**|Single segmented conversation transcript|
|**Confidence**|Minimum 85% required for publishing results|

**Analysis Output Schema**

|**Field**|**Type**|**Description**|
| :- | :- | :- |
|**intent**|string|Primary customer purchase intent|
|**products**|array|Products discussed or requested|
|**budget**|string|Budget range if mentioned|
|**objections**|array|List of objections raised|
|**competitors**|array|Competitor brands mentioned|
|**closingAttempt**|boolean|Whether a close was attempted|
|**outcome**|string|Sale made / Lost / Follow-up needed|
|**confidence**|number|AI confidence score 0–100|

## **AI-07  Salesperson Performance Scoring**
**Scoring Dimensions**

|**Dimension**|**What is Measured**|
| :- | :- |
|**Greeting Score**|Warmth, professionalism, and speed of initial greeting|
|**Discovery Score**|Quality and depth of needs-finding questions asked|
|**Product Knowledge**|Accuracy and depth of product explanations given|
|**Objection Handling**|How effectively objections were addressed and resolved|
|**Closing Score**|Number and quality of closing attempts made|

## **AI-08 / AI-09 / AI-10  Aggregated Intelligence**

|**Level**|**AI Outputs**|**Consumer**|
| :- | :- | :- |
|**Recording (AI-08)**|Total conversations, top intent, top objection, missed opportunities|Salesperson & Manager|
|**Store (AI-09)**|Top products, top objections, conversion trends, store ranking|Store Manager & Brand Admin|
|**Brand (AI-10)**|Store comparisons, regional trends, coaching needs, revenue risks|Brand Admin & C-Suite|



|**MODULE 2 — BACKEND PLATFORM**|
| :- |

|Objective: Provide REST APIs, data storage, async processing orchestration, and analytics aggregation for the full SAMAA platform.|
| :- |

## **Backend Architecture**

|**Frontend (Next.js)**|
| :-: |
|**API Gateway**|
|**NestJS Application Server**|
|**PostgreSQL + pgvector**|
|**Redis Queue (BullMQ)**|
|**AI Worker Processes**|

## **Technology Stack**

|**Layer**|**Technology**|
| :- | :- |
|**API Framework**|NestJS (TypeScript)|
|**Database**|PostgreSQL with Prisma ORM|
|**Vector Search**|pgvector extension|
|**Job Queue**|BullMQ + Redis|
|**File Storage**|AWS S3 or Cloudflare R2|
|**Auth**|JWT with role-based access control|

## **API Reference**

### **BE-01  Authentication**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**POST**|/auth/login|Login and receive JWT token|
|**POST**|/auth/refresh|Refresh an expired JWT token|
|**POST**|/auth/logout|Invalidate current session|

### **BE-02  Brand Management**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**GET**|/brands|List all brands (Super Admin)|
|**POST**|/brands|Create a new brand|
|**GET**|/brands/:id|Get brand details|
|**PUT**|/brands/:id|Update brand information|

### **BE-03  Store Management**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**GET**|/stores|List stores for the current brand|
|**POST**|/stores|Create a new store|
|**GET**|/stores/:id|Get store details|
|**GET**|/stores/:id/metrics|Get aggregated store metrics|

### **BE-04  Salesperson Management**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**GET**|/salespeople|List all salespeople in a store|
|**POST**|/salespeople|Add a new salesperson|
|**GET**|/salespeople/:id|Get salesperson profile|
|**GET**|/salespeople/:id/performance|Get performance metrics|

### **BE-05 / BE-07 / BE-08  Recordings & Transcripts**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**POST**|/recordings/upload|Upload audio file and initiate processing|
|**GET**|/recordings/:id|Get recording metadata and status|
|**GET**|/recordings/:id/status|Poll processing pipeline status|
|**GET**|/recordings/:id/transcript|Retrieve full timestamped transcript|
|**GET**|/recordings/:id/conversations|List all conversations in recording|

### **BE-09  Conversation Analysis**

|**Method**|**Endpoint**|**Description**|
| :- | :- | :- |
|**GET**|/conversations/:id|Get conversation details|
|**GET**|/conversations/:id/analysis|Get full AI analysis for conversation|

## **BE-06  Processing Queue**
**Pipeline Stages**

|**Stage**|**Description**|
| :- | :- |
|**UPLOADED**|File received and stored; job queued|
|**PREPROCESSING**|Audio normalization and format conversion|
|**TRANSCRIBING**|Parakeet ASR running|
|**DIARIZING**|NeMo speaker separation|
|**ANALYZING**|LLM conversation analysis running|
|**COMPLETED**|All data stored; dashboards updated|
|**FAILED**|Error encountered; retry queued|

## **Database Schema**
**Core Tables**

|**Table**|**Key Fields**|
| :- | :- |
|**brands**|id, name, created\_at|
|**stores**|id, brand\_id, name, location, working\_hours|
|**salespeople**|id, store\_id, name, role, shift|
|**recordings**|id, salesperson\_id, file\_url, duration, status, uploaded\_at|
|**transcript\_segments**|id, recording\_id, speaker, start, end, text|
|**conversations**|id, recording\_id, start, end, segment\_count|
|**conversation\_analysis**|id, conversation\_id, intent, products, objections, outcome, confidence|
|**metrics\_daily**|id, entity\_id, entity\_type, date, conversation\_count, avg\_score|
|**metrics\_weekly**|id, entity\_id, entity\_type, week, conversion\_rate, top\_objection|



|**MODULE 3 — FRONTEND PLATFORM**|
| :- |

|Objective: Provide intuitive dashboards and drill-down views for every organizational level, from brand-wide intelligence down to individual conversation analysis.|
| :- |

## **Frontend Technology Stack**

|**Layer**|**Technology**|
| :- | :- |
|**Framework**|Next.js + TypeScript|
|**Styling**|Tailwind CSS|
|**State Management**|Redux Toolkit or Zustand|
|**Charts**|Recharts|
|**UI Components**|shadcn/ui|
|**Icons**|Lucide React|

## **Page Specifications**

### **FE-01  Login & Authentication**
- Login page with email and password
- Forgot password / reset flow
- JWT stored in secure HTTP-only cookie
- Role-based redirect after login (Brand Admin → Brand Dashboard, etc.)

### **FE-02  Brand Dashboard**

|**Component**|**Content**|
| :- | :- |
|**Summary Cards**|Total stores, salespeople, conversations, brand conversion score|
|**Store Ranking Table**|All stores ranked by average performance score|
|**Trend Charts**|Conversation volume and conversion rate over time|
|**Top Objections**|Most common objections across all stores|
|**Coaching Alerts**|Stores and salespeople flagged for coaching|

### **FE-03  Store Dashboard**
- Store header with location and contact information
- KPI cards: performance score, conversation volume, top objection
- Salesperson performance table with drill-down links
- Daily and weekly trend charts
- Recordings upload status table

### **FE-04  Salesperson Dashboard**
- Profile header with name, role, and shift information
- KPI cards: conversations handled, closing rate, average score
- Skill radar chart across all five scoring dimensions
- Recordings list with score preview and status badge
- Coaching recommendation panel with prioritized suggestions

### **FE-05  Recording Listing Page**

|**Filters**|Date range, processing status, duration range|
| :- | :- |
|**Table Columns**|Date, Duration, Conversations Detected, Avg Score, Status Badge|
|**Actions**|View Details, Download Audio, Re-process|
|**Status Badges**|Uploaded, Processing, Transcribed, Analyzed, Completed, Failed|

### **FE-06  Recording Detail Page**
- Recording header: date, salesperson, duration, processing status
- Summary cards: conversation count, top intent, top objection, missed opportunities
- Interactive conversation timeline showing each customer interaction
- Transcript viewer with speaker labels and timestamps
- AI Insights panel: intent, budget, objections, outcome per conversation

### **FE-07  Conversation Detail Drawer**
- Full conversation transcript with speaker-colored labels
- AI-generated one-paragraph summary
- Objections list with suggested responses
- Products discussed section
- Coaching notes generated from conversation behavior

### **FE-08  Coaching Dashboard**

|**Section**|**Content**|
| :- | :- |
|**Skill Scores**|Numerical scores with trend vs. prior period for all 5 dimensions|
|**Improvement Areas**|AI-identified weakest areas with specific examples from conversations|
|**Recommendations**|Prioritized action items for the salesperson or manager|
|**Historical Trend**|Score improvement over the past 30 / 60 / 90 days|

### **FE-09  Search Experience**
- Natural language search across all conversations
- Example queries: 'price objections last week', 'lost sales', 'competitor mentions'
- Results shown as conversation cards with highlighted transcript snippets
- Filters: date range, store, salesperson, outcome
- Powered by pgvector semantic similarity search


# **Non-Functional Requirements**

## **Performance**

|**Metric**|**Target**|**Priority**|
| :- | :- | :- |
|Audio upload initiation|**< 30 seconds**|**P0**|
|Dashboard load time|**< 3 seconds**|**P0**|
|Analysis result retrieval|**< 1 second**|**P1**|
|Transcript load time|**< 2 seconds**|**P1**|
|Search response time|**< 500ms**|**P1**|

## **Scalability**

|<p>**100**</p><p>Brands</p>|<p>**1,000**</p><p>Stores</p>|<p>**10,000**</p><p>Salespeople</p>|
| :-: | :-: | :-: |

|Target capacity: Millions of conversations with sub-second analysis retrieval.|
| :- |

## **Security**
- JWT authentication with short token expiry and refresh rotation
- Role-based access control enforced at API gateway level
- All audio files stored encrypted at rest (AES-256)
- Signed URLs for time-limited audio access (15-minute expiry)
- All data in transit encrypted via TLS 1.3
- Audit logging for all data access and admin actions


# **MVP Delivery Plan**

|The build order is designed bottom-up: AI pipeline first, then backend APIs, then frontend dashboards. Each sprint produces a shippable increment.|
| :- |

## **Sprint Plan**

|**Sprint**|**Focus**|**Deliverables**|
| :- | :- | :- |
|**Sprint 1**|**Backend Foundations**|Authentication, Brand/Store/Salesperson CRUD, Audio upload, DB schema|
|**Sprint 2**|**AI Pipeline**|Parakeet STT integration, NeMo diarization, conversation segmentation|
|**Sprint 3**|**LLM Analysis**|Llama 3.3 analysis, intent/objection/outcome extraction, recording summaries|
|**Sprint 4**|**Frontend Core**|Brand, Store, and Salesperson dashboards, Recording listing page|
|**Sprint 5**|**Detail Experience**|Recording detail page, transcript viewer, AI insights panel, coaching dashboard|
|**Sprint 6**|**Intelligence Layer**|Store and Brand aggregations, search with pgvector, export and reporting|

## **Definition of Done — Per Sprint**

|**Sprint**|**Definition of Done**|
| :-: | :- |
|**S1**|All CRUD endpoints tested, audio upload functional, DB migrations applied|
|**S2**|8-hour audio processed to transcript in < 10 min; speaker labels accurate|
|**S3**|95%+ of conversations produce valid structured JSON analysis output|
|**S4**|All dashboard pages load with real data, navigation drill-down working|
|**S5**|Recording detail page shows transcript + AI insights inline; coaching visible|
|**S6**|Brand and store dashboards aggregate correctly; search returns relevant results|


# **Appendix — Glossary**

|**Term**|**Definition**|
| :- | :- |
|**ASR**|Automatic Speech Recognition — converts audio speech to text|
|**Diarization**|The process of separating audio by speaker identity|
|**Conversation Segment**|A discrete customer interaction extracted from a longer recording|
|**Intent**|The primary purchase goal or inquiry of a customer in a conversation|
|**Objection**|A stated reason from the customer not to purchase|
|**pgvector**|PostgreSQL extension enabling vector-similarity semantic search|
|**BullMQ**|A Redis-backed job queue library for Node.js async processing|
|**JWT**|JSON Web Token — a compact token standard for stateless authentication|
|**LLM**|Large Language Model — the AI used for conversation analysis|
|**Parakeet**|NVIDIA's 1.1B parameter multilingual ASR model|
|**NeMo**|NVIDIA's neural module framework for speech and NLP models|

Page   |  SAMAA PRD  |  Internal Use Only
