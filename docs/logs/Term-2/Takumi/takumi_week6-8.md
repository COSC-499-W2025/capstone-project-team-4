## Week 6-8 – Individual Log (Takumi)

<img width="1110" height="640" alt="Screenshot 2026-03-01 at 21 53 03" src="https://github.com/user-attachments/assets/cb65e92c-8b09-4630-a417-3ae49675ef22" />


### Overview  
During Weeks 6 to 8, I worked on building the Portfolio API feature. This feature pulls together all analyzed project data and allows users to generate, edit, and view their portfolio. I built three endpoints from scratch and followed the same service and repository structure that we’ve been using in the project.

### Coding Tasks  
- Built `POST /api/portfolio/generate`. This endpoint collects a user’s projects, skills, resume highlights, and experiences, then uses AI (with a template fallback if needed) to create a portfolio with a title, summary, and structured content. It saves or updates the portfolio in the database.  
- Built `PUT /api/portfolio/{portfolio_id}/edit`. This lets logged in users update parts of their portfolio, such as the title, summary, or content. It checks ownership and returns 403 if the user is not the owner and 404 if the portfolio does not exist.  
- Built `GET /api/portfolio/{portfolio_id}` as a public endpoint. It does not require login, so users can share their portfolio link with recruiters or others.  
- Created `PortfolioUpdate` for partial updates and `PortfolioResponse` for returning data through the API.  
- Added the `Portfolio` model with a JSON content field.  
- Implemented `PortfolioRepository` and `PortfolioService` to keep the structure consistent with the rest of the project.  

### Testing and Debugging Tasks  
- Wrote 26 unit tests covering the generator logic, service layer, and all three portfolio endpoints.  
- Fixed an issue where some endpoint tests were hanging. The problem was that the authentication fixture was connecting to the real PostgreSQL database. I fixed this by overriding `get_current_user` in tests so authentication could be mocked without connecting to the database.  
- Debugged a problem where the generated portfolio showed 0 projects. After tracing it back, I realized the analysis routes did not require authentication, so `Project.user_id` was never being set. I fixed this by adding `get_current_user` to all analysis routes.  
- Investigated another issue where editing a portfolio returned a 200 success response but the changes did not appear in the GET endpoint. At first I thought it was a database or update logic issue, but it turned out to be malformed JSON in the request body. I was missing closing brackets. This was a good reminder to always double check the request payload before assuming the backend is broken.  

### Reviewing and Collaboration Tasks  
Reviewed PRs related to incremental files addition, resume services (adds the business logic and API surface for full resume generation), textual project showcase, and tech stack analysis enhancements (separated detection APIs, upload optimization flags, and contributor-level analysis).

### Connection to Previous Week  
Last week, I finished implementing the snapshot endpoints. After completing that feature, I shifted my focus this week to another Milestone 2 requirement: building the portfolio endpoints.

### Plan for Next Week  
Since Milestone 2 is done, I will... :
- Review the Milestone 3 requirements and break them down into actionable tasks
- Discuss implementation strategy with the team and divide responsibilities
- Continue reviewing teammates’ PRs and provide feedback

### Issues / Blockers  
I spent a fair amount of time thinking there was a problem with how SQLAlchemy tracks changes in JSON fields because updates were not persisting. I even tried adding special handling to track changes. In the end, the real issue was malformed JSON in the request. Once I fixed the request body, everything worked fine. 
