# JobPilot 🚀

**AI-Powered Job Hunting Copilot** - An intelligent agent that can browse, scrape, search, summarize, and act on job opportunities automatically.

## 🎯 Vision

JobPilot is an agentic tool framework designed to revolutionize job hunting by automating the tedious parts while enhancing the strategic aspects. It acts as your personal job hunting assistant that works 24/7 to find, analyze, and apply to relevant opportunities.

## 🏗️ Architecture

### Core Components

#### 1. Web Automation Layer
- **BrowserUse/Playwright**: Handles web navigation, scraping, and form automation
- **Capabilities**: Login management, dynamic content scraping, application form filling
- **Target Sites**: LinkedIn, Indeed, Glassdoor, company career pages

#### 2. AI Orchestration Layer
- **LangChain**: Orchestrates multi-agent workflows and tool integration
- **Agent Types**:
  - Discovery Agent: Job search and extraction
  - Matching Agent: Skill-job compatibility analysis
  - Tailoring Agent: Resume/cover letter customization
  - Outreach Agent: Recruiter contact and messaging
  - Application Agent: Automated form submission

#### 3. Knowledge Management Layer
- **LlamaIndex**: Organizes and retrieves personal job search data
- **Data Sources**:
  - Personal resumes and cover letters
  - Company and recruiter notes
  - Application history and outcomes
  - Interview experiences and feedback

#### 4. Intelligence Layer
- **Ollama**: Local LLM for privacy-first processing
- **Cloud LLMs**: Claude/GPT-4 for complex reasoning tasks
- **Capabilities**: Semantic matching, content generation, decision making

#### 5. Data Storage Layer
- **Vector Database**: Semantic search for jobs and contacts
- **Structured Database**: Application tracking and metadata
- **File Storage**: Documents, screenshots, and artifacts

#### 6. Integration Layer
- **Job APIs**: LinkedIn, Indeed, Glassdoor integration
- **Communication APIs**: Email, LinkedIn messaging
- **Calendar APIs**: Interview scheduling

## 🔄 Workflow Design

### Phase 1: Discovery
```
Job Board Scraping → Content Extraction → Semantic Analysis → Relevance Scoring
```
- Automated browsing of job boards
- Extraction of job descriptions, requirements, and metadata
- Semantic matching against user skills and preferences
- Storage in vector database with relevance scores

### Phase 2: Intelligence
```
Job Analysis → Skill Gap Analysis → Company Research → Strategic Planning
```
- Deep analysis of job requirements vs. user profile
- Identification of skill gaps and improvement areas
- Company culture and hiring process research
- Personalized application strategy development

### Phase 3: Customization
```
Resume Tailoring → Cover Letter Generation → Portfolio Curation → Application Prep
```
- Dynamic resume optimization for each opportunity
- Personalized cover letter generation
- Relevant portfolio/project highlighting
- Interview preparation materials

### Phase 4: Outreach
```
Recruiter Identification → Contact Research → Message Crafting → Engagement Tracking
```
- LinkedIn recruiter and employee identification
- Contact information gathering and verification
- Personalized outreach message creation
- Engagement tracking and follow-up scheduling

### Phase 5: Application
```
Form Analysis → Automated Filling → Document Upload → Submission Tracking
```
- Application form structure analysis
- Automated form completion where possible
- Resume/cover letter upload and formatting
- Application status monitoring

## 🛠️ Technology Stack

### Core Framework
- **Python 3.11+**: Primary language
- **LangChain**: Agent orchestration
- **LlamaIndex**: Knowledge management
- **FastAPI**: API and web interface

### Web Automation
- **BrowserUse**: Primary web automation
- **Playwright**: Backup automation framework
- **BeautifulSoup**: Static content parsing

### AI & ML
- **Ollama**: Local LLM hosting
- **OpenAI/Anthropic**: Cloud LLM APIs
- **Sentence Transformers**: Embeddings
- **spaCy**: NLP processing

### Data & Storage
- **Qdrant/Pinecone**: Vector database
- **SQLite/PostgreSQL**: Relational database
- **Pydantic**: Data validation

### APIs & Integrations
- **LinkedIn API**: Professional networking
- **Outlook API**: Email automation
- **Calendar APIs**: Scheduling
- **Job Board APIs**: Data access

## 📋 Development Roadmap

### ✅ Phase 1: Foundation (COMPLETED)
- [x] Project structure and README
- [x] Core dependencies and environment setup
- [x] Configuration management system
- [x] Logging infrastructure
- [x] Data models and validation
- [x] Basic testing and validation

> **Status:** COMPLETED ✅ - [See Phase 1 Documentation](docs/phase-1-foundation-complete.md)

### 🔍 Phase 2: Discovery Engine
- [ ] Job board scraper development
- [ ] Content extraction and parsing
- [ ] Semantic matching algorithm
- [ ] Vector database integration
- [ ] Basic job filtering and ranking

### 🧠 Phase 3: Intelligence Layer
- [ ] User profile management
- [ ] Skill gap analysis
- [ ] Company research automation
- [ ] Resume tailoring engine
- [ ] Cover letter generation

### 🤝 Phase 4: Outreach Automation
- [ ] LinkedIn contact discovery
- [ ] Recruiter identification
- [ ] Message personalization
- [ ] Outreach campaign management

### 📝 Phase 5: Application Automation
- [ ] Form recognition and filling
- [ ] Document upload automation
- [ ] Application tracking
- [ ] Status monitoring

### 🎯 Phase 6: Advanced Features
- [ ] Interview preparation
- [ ] Salary negotiation insights
- [ ] Career progression planning
- [ ] Network analysis and recommendations

### 🌟 Phase 7: Polish & Deployment
- [ ] Web interface development
- [ ] Mobile companion app
- [ ] Cloud deployment options
- [ ] Enterprise features

## 🚦 Getting Started

### Prerequisites
- Python 3.11+
- Node.js (for web automation)
- Git
- Conda or UV for dependency management

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/JobPilot.git
cd JobPilot

# Set up environment
conda create -n jobpilot python=3.11
conda activate jobpilot

# Install dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy `.env.example` to `.env`
2. Configure API keys and settings
3. Set up local LLM with Ollama
4. Initialize databases

## 📁 Project Structure
```
JobPilot/
├── src/
│   ├── agents/          # LangChain agents
│   ├── scrapers/        # Web scraping modules
│   ├── knowledge/       # LlamaIndex components
│   ├── automation/      # Browser automation
│   ├── apis/           # External API integrations
│   └── utils/          # Utility functions
├── data/
│   ├── profiles/       # User profiles and resumes
│   ├── jobs/          # Scraped job data
│   └── contacts/      # Recruiter and contact info
├── tests/              # Test suites
├── docs/              # Documentation and progress
├── scripts/           # Utility scripts
└── web/               # Web interface
```

## 🤝 Contributing

This is currently a personal project, but contributions and suggestions are welcome! Please check the roadmap and open issues for areas where help is needed.

## 📄 License

MIT License - See LICENSE file for details.

## 📞 Contact

For questions, suggestions, or collaboration opportunities, please open an issue or reach out directly.

---

**Note**: This project is in active development. Features and architecture may evolve as the system is built and tested.
