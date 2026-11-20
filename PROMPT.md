# Prompt Log

The full log of how Ledgerly was built with Claude (Anthropic), in order. Each entry has my prompt (exactly as I typed it), a short summary of what the AI gave back, and what I did with it.

---

## Phase 1: Finding the idea

### Prompt 1
> *(attached the assignment instructions)* these are the instructions of the assignment. Go through it very carefully and come up with good and unique ideas for this assignment.

**AI response:** Six ideas based on my life and the rubric: a pizza-rush kitchen simulator, a bug-fixing escape room, a "Hallucination Hunter" quiz, a TCF French speaking coach, a group-project fairness meter, and a rumour-spread simulator. Each came with a version-by-version plan.

**Outcome:** Creative, but mostly games. Not what I wanted.

### Prompt 2
> give me the idea that is useful in everyday life

**AI response:** "Use It Up", a pantry and expiry tracker with recipe suggestions, plus two alternatives (a shift and pay planner and a roommate bill splitter).

**Outcome:** Useful but felt common.

### Prompt 3
> forget about it. Come up with some other unique ideas that you have not given to anybody else

**AI response:** Said it can't see other people's chats, so it couldn't promise that, then gave less common ideas: Deadline Liar, Regret Meter, Walk or Wait (a Barrie winter weather helper), Quiet Corner (a noise map of study spots), Closet Ghost, and a Canadian slang decoder.

**Outcome:** More original, but some felt like novelty apps.

### Prompt 4
> i don't want fun games, Give me something useful

**AI response:** Practical tools: a job application tracker with resume matching, a return and warranty deadline tracker, a pay stub checker, an important dates vault, and a lease red-flag checker.

### Prompt 5
> something else

**AI response:** A course outline organizer with a grade calculator, a cheapest-store grocery finder, an official letter explainer, a message polisher, and a **simple invoice maker for freelancers and small businesses**.

### Prompt 6
> something else maybe related to travel and food

**AI response:** A menu scanner and diet checker, a road-trip meal stop planner, a group dinner matcher, a trip meal planner, and a multi-currency trip expense splitter.

**Outcome:** I went back to the invoice maker from prompt 5. It fits my entrepreneurial program and solves a real problem.

### Prompt 7
> 5. Simple Invoice Maker for freelancers and small businesses ... explain this in detail

**AI response:** A full breakdown: the problem, the user flow, features, the HST calculation with a worked example, how statuses and "overdue" work, database tables, the tech stack, a version plan, edge cases to test, example prompts, and future improvements.

**Outcome:** Decided on the invoice app.

### Prompt 8
> how long will this take to build?

**AI response:** About 15–25 hours over 5–7 days, broken down by phase, with a 12–15 hour "core only" option.

---

## Phase 2: Scoping and design

### Prompt 9
> I have only 2 hrs. Concise the project accordingly. Keep the necessary features for this assignment which can get me full marks. Use sql server and django for the backend. And vanilla JS for frontend. Whatever code you generate should be optimized and precise. It should look like iot was written by a human and not an AI. Write humanized comments everywhere and make sure to remove the instructions. Keep the UI soothing and professional, sleek and elegant. I want you to give me a few designs and overview of the application first. What pages it would have and what features to keep ? The features should be of intermediate level.

**AI response:** Reminded me that the README still has to disclose AI use, and warned that SQL Server needs the `mssql-django` package and an ODBC driver. Proposed the name **Ledgerly**, five pages (Dashboard, Clients, Invoice builder, Invoice view, Settings), an intermediate feature list, features to cut (going to Future Improvements), a commit plan, and three colour themes as previews.

**Outcome:** Liked the plan. The designs looked too basic.

### Prompt 10
> give me some more preview designs, these are very basic designs, add some related icons in the application. Think like and expert and experience UI / UX designer and also make use of three.js connector to come up with some animations for the dashboard

**AI response:** Three much more detailed dashboards (Sage studio, Midnight ledger, Ivory editorial) with icons, KPI cards with trends, a cash flow chart, a collection-rate ring, recent invoices and a "due this week" list. It also built a live three.js scene: revenue bars growing in, a floating "PAID" invoice and orbiting coins. It explained the UX reasoning and suggested making the 3D part the last commit so it could be dropped if time ran out.

### Prompt 11
> I've to make 5 commits at least for this assignment as it a requirement. And help me initialize the git repo for this project from vs code interface

**AI response:** Step-by-step VS Code instructions (Initialize Repository, stage, commit, Publish Branch, Sync), a `.gitignore` for Django, and a seven-commit plan with message examples.

**Outcome:** I created the repo, added the `.gitignore` and made my first commit.

### Prompt 12
> I am using microsoft SQl server 20 and it is already installed. Design will be B. Make sure to use better fonts, this looks very basic

**AI response:** Started building with design B (dark "Midnight ledger"). Swapped the fonts to Plus Jakarta Sans (body), Sora (headings and numbers) and JetBrains Mono (invoice numbers). Checked package versions and chose Django 5.2 LTS with `mssql-django` 1.8, because the newer 2.0 release changed database drivers.

### Prompt 13
> can you access my vs code? I am currently in VibeCodingProject folder...

### Prompt 14
> C:\Professional\GeorgianCollege\Semester-5\Introduction To AI\VibeCodingProject this is the project path on my local computer

**AI response:** Got access to the folder and wrote the project into it one stage at a time. After each stage I ran the app, checked it, and committed it myself from VS Code.

---

## Phase 3: Building in stages

Each stage was generated, run, tested and committed before the next one started.

| Stage | What was built | Commit |
|---|---|---|
| 1 | Django project, SQL Server settings from `.env`, models (BusinessProfile, Client, Invoice, InvoiceItem), money maths in `calculations.py`, dark layout with sidebar, Settings page | Set up Django project with SQL Server, models and app layout |
| 2 | Clients page (search, add/edit pop-up, safe delete), invoices list with status tabs, invoice builder with line-item formset and live totals | Add clients page and invoice builder with live totals |
| 3 | Invoice page drawn like paper, Draft → Sent → Paid actions, edit and delete only for drafts, print / PDF stylesheet, reminder email link | Add invoice view, status flow and print layout |
| 3b | "Send invoice" emails the invoice to the client (HTML + plain text) through SMTP, keeps it a draft if sending fails, resend button, email settings in `.env` | Send invoices to clients by email |
| 4 | Dashboard KPIs, six-month bar chart, collection ring, recent invoices filter, due this week, `seed_demo` command | Add dashboard stats and demo data |
| 5 | Fixes from testing (below) and 17 automated tests | Fix rounding and number formatting, add tests |
| 6 | three.js 3D cash flow hero on the dashboard | Add animated 3D cash flow hero to dashboard |
| 6b | Removed repeated numbers from the dashboard (see prompt 16) | Remove repeated stats from dashboard |
| 6c | Invoices list paginated (10 per page) without full page reloads (see prompt 17) | Paginate invoices list without page reloads |
| 6d | Reminder emails sent from the app with the invoice PDF attached (see prompt 18) | Email reminders with the invoice PDF attached |
| 6e | Comment clean-up across the project (see prompt 19) | Clean up and explain code comments |
| 6f | Doctype moved to the first line of `base.html` (see prompt 20) | Put the doctype first in the base template |
| 7 | README, screenshots, this prompt log | Add README, screenshots and prompt log |

---

### Prompt 15 (while testing stage 3)
> when I click send invoice, Please change the code so that the invoice is sent to the client through email. please update the code and get back to me

**AI response:** Replaced "Mark as sent" with a real **Send invoice** button. It added `invoices/emails.py`, an email-safe HTML template (inline styles, because email apps ignore stylesheets) plus a plain-text version, and SMTP settings read from `.env` (with instructions for a Gmail App Password). With no settings, emails are printed in the terminal instead. If sending fails, the invoice stays a draft and an error explains why, so an invoice is never marked sent when it wasn't. It also added a resend button, a "Sending..." state so the button can't be clicked twice, and two tests (the email goes to the right client, and a failed send leaves the invoice as a draft).

**Outcome:** Committed as its own step, separate from stage 3.

---

### Prompt 16 (while testing stage 6)
> you look at the final design, same things are repeating again and again ?

**AI response:** Agreed. Listed every repeat: "collected this month" in both the hero and a KPI card, the month-over-month trend twice, the overdue count and total three times (header, hero, card), the collection rate as a ring and as a sentence, and the 3D bars duplicating the 2D bar chart. It gave each number a single place: the hero covers money coming in (this month, trend, and a labelled six-month strip under the 3D bars), the four cards cover outstanding, overdue, collection rate (now a small progress bar) and days to get paid, and the 2D chart and ring were removed. It showed a screenshot of the new layout before changing my files.

**Outcome:** Committed as its own step after stage 6.

### Prompt 17 (while testing the invoices page)
> add pagination in the invoices tab so that only 10 rows appear on 1 page. Don't refresh the entire page just change the data of the invoices when the page changes. It is looking very messy rn

**AI response:** Added server-side pagination (Django's `Paginator`, 10 per page, with page numbers like 1 … 4 5 6 … 12 for long lists). The table was moved into its own small template. When JavaScript asks for a page with an `X-Requested-With: fetch` header, the view sends back only that part, and the script swaps it in. Tabs and search work the same way. Search moved from the browser to the database, because a browser-side search would only have searched the 10 rows on screen. The address bar updates with `history.pushState`, so refresh and the back button still work, and if a request fails it falls back to a normal page load. Rows were made a little shorter, and two tests were added (10 per page, and search finding invoices beyond page 1).

**Outcome:** Committed as its own step after the dashboard cleanup.

### Prompt 18 (while testing the invoice page)
> when I click email client, it should send the invoice as an attachment to the client along with a polite request msg which is already there. Write something like your invoice is attached below. Write the email professionally and politely as if it's just a reminder

**AI response:** Replaced the `mailto:` link with a real reminder email sent by the app. It added `invoices/pdf.py`, which builds the invoice PDF with ReportLab (chosen because it installs cleanly on Windows, unlike PDF tools that need a browser engine), and attached that PDF to both the invoice email and the reminder. The reminder text is polite and professional, and it changes depending on whether the invoice is due soon or already past due ("…is now 5 days past due. For your convenience, a copy of the invoice is attached…"). The email layouts were moved into one shared base template so the invoice and reminder emails don't repeat each other. The dashboard's "Due this week" reminder buttons now send the same email and return you to the dashboard. While testing, it also fixed the sample data: the activity timeline said invoices were created *after* they were sent, because `created_at` was always "now". Three tests were added (PDF attached, reminder text and attachment, and no reminders for drafts).

**Outcome:** Committed as its own step. `reportlab` was added to `requirements.txt`.

### Prompt 19 (before the final docs)
> email is working now, before moving forward, I want you to go through all the files of this project and remove all the instruction comments and write humanized comments explaining the code to the prof. PLEASE remove the instructions and examples comments as I won't be checking the all the files myself. Don't break my trust

**AI response:** Went through every Python, JavaScript, HTML, text and config file. It rewrote comments that read like setup instructions or usage examples (for example, the `seed_demo` docstring listing commands to run, and step-by-step Gmail setup in `.env.example`) so they explain what the code does and why, and kept the setup steps in the README where they belong. It corrected two comments that had become inaccurate (one said no PDF library was needed, from before ReportLab was added, and one described the 3D card as showing the latest invoice). It added short explanations where there were none: what each table in `models.py` is for, why actions only accept POST, how the invoice builder's hidden DELETE boxes work, and why the email templates use inline styles. It then searched all files for leftover instruction-style comments, re-ran the 22 tests, and checked my folder's files hadn't changed since the last commit before writing anything. Django's own generated files (`manage.py`, the migration) were left as Django wrote them.

**Outcome:** Committed as its own step.

### Prompt 20
> fix the errors in base.html

**AI response:** Explained that the template itself was valid and the app ran fine. The red marks came from VS Code checking Django templates as plain HTML. It moved `<!DOCTYPE html>` to the first line (it had been after `{% load static %}`, which HTML checkers flag), and added a local `.vscode/settings.json` (not committed) so VS Code treats the templates as Django templates. It also suggested installing the Django extension for VS Code.

---

## Phase 4: Testing and fixing

Problems found while testing, and how they were fixed:

1. **Live total one cent off.** For 0.5 × $2.01 the browser showed $1.00 but the saved invoice said $1.01. Cause: `Math.round(value * 100) / 100` in JavaScript, where 1.005 × 100 is really 100.4999... Fix: round with exponent notation (`Math.round(value + "e2")`) so it matches Python's `ROUND_HALF_UP`.
2. **Mixed number formats.** The dashboard showed "$5 769" while tables showed "$1,356.00", because `intcomma` follows the `en-ca` locale. Fix: one custom `|cad` template filter used everywhere, plus a test.
3. **Table headers not right-aligned.** `.table th { text-align: left }` beat the `.right` class. Fix: a more specific `.table .right` rule.
4. **Toast messages covered the "New invoice" button.** Fix: moved them to the bottom right.
5. **Sidebar stopped halfway down long pages.** Fix: painted the sidebar colour on the page shell.
6. **Reminder links loaded the business profile once per invoice.** Fix: load it once and pass it in.
7. **Dashboard showed the same numbers two or three times** after the 3D hero was added. Each number now appears once (prompt 16).
8. **Activity timeline out of order on sample invoices** ("Created Nov 19" listed after "Sent Nov 12"). The demo data command now sets the created date to the issue date.
9. **3D camera too far, then too close.** Adjusted the field of view and camera position until the bars and the invoice card fit the hero.

---

## What I'd ask differently next time

- Give the constraints (time, stack, level, look) in the very first prompt instead of narrowing down over six messages
- Ask for tests together with each feature, not at the end
- Ask the AI to look at the page itself (screenshots) after every UI change, since that's where most bugs showed up
