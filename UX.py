import Gmail_Interface
import AI_API
import VectorDB
import sys

def main():
    print("Starting program...")
    service = Gmail_Interface.start_up()
    vector_db = VectorDB.initialize_VectorDB()
    # gmail_Objects = Gmail_Interface.get_unread_emails(service)
    email_objects = Gmail_Interface.get_unread_email_objects(service)
    VectorDB.add_emails_to_vectorDB(vector_db, email_objects)
    while True:
        print("What do you want to do? Type 'help' for a list of commands")
        user_input = input("> ")

        if user_input == "exit":
            break

        elif user_input == "send an email":
            print("What do you want to send? Remember, it's only to yourself")
            user_input = input("> ")
            Gmail_Interface.send_email(service, user_input)

        elif user_input == "summarize emails":
            print(AI_API.summarize_Emails(email_objects))

        elif user_input == "I'd like to ask a question about a specific email":
            print("What is the email address that sent the email you're looking for? Type None if you don't know")
            sender = input("> ")

            if sender.strip().lower() == "none":
                sender = None

            print("And what is your question?")
            question = input("> ")
            vector_Response = VectorDB.query_vectorDB_combined(vector_db, question, sender)
            body = VectorDB.extract_body_text_from_results(vector_Response)
            from_address = VectorDB.extract_from_address_from_results(vector_Response)
            output = AI_API.answer_question_with_context(question, from_address, body, 5000)
            print(output)

        elif user_input == "help":
            print("""
            send an email
            summarize emails
            I'd like to ask a question about a specific email
            exit
            restart
            send summary email
            """)

        elif user_input == "exit":
            break

        elif user_input == "restart":
            service = Gmail_Interface.start_up()
            vector_db = VectorDB.initialize_VectorDB()
            gmail_Objects = Gmail_Interface.get_unread_emails(service)
            email_objects = Gmail_Interface.get_unread_email_objects(service)
            VectorDB.add_emails_to_vectorDB(vector_db, email_objects)

        elif user_input == "send summary email":
            summary = AI_API.summarize_Emails(email_objects)
            Gmail_Interface.send_email(service, summary)
        

'''
Old Code, not used

        # test only works when reducing the number of max tokens in AI_API.py
        elif user_input == "test summarize on small token count":
            long_email = """
Subject: Strategic Product Update – H2 Planning, Vision Alignment, and Execution Framework

Hi team,

I hope this message finds you well. As we close out Q2 and transition into the second half of the year, I want to take a moment to reflect on our progress, highlight strategic initiatives, and align on our roadmap going forward. Please read this note carefully — it's long, but it lays the groundwork for our H2 goals, priorities, and execution model across Product, Engineering, Design, and GTM.

**Recap of H1 Performance and Learnings**

First, I want to recognize the outstanding work that went into launching the Workflow Intelligence Suite in May. The collaboration across teams — from Research to Infra to Product Marketing — was some of the best we’ve seen. We’ve already onboarded 140+ customers into early access, and feedback indicates significant ROI, especially among enterprise finance users. That said, we've also identified key gaps around onboarding clarity, reporting latency, and actionability — and we must directly address those before GA.

Looking more broadly at our H1 performance:
- We beat our activation rate targets by 18% across the SMB and mid-market segments.
- User retention after day 7 remains a core challenge, especially for technical users who expect greater integration flexibility.
- Our NPS held steady at 43 (versus a goal of 50), with support responsiveness and roadmap transparency being frequent concerns.
- Churn decreased by 9% quarter-over-quarter, largely due to improvements in feature discoverability and product-led support.

**Strategic Focus for H2**

Our North Star for H2 remains unchanged: **Build the most intelligent, extensible, and trustworthy platform for workflow automation in data-heavy industries.** To that end, we are organizing our roadmap around three pillars:

1. **Deepen Core Platform Value**
   - Modularize the rules engine to allow for vertical-specific plug-ins.
   - Invest in ML-driven automation triggers with tighter auditability.
   - Expand our library of prebuilt integrations by 30%, prioritizing financial and logistics APIs.

2. **Accelerate User Time-to-Value**
   - Launch guided onboarding paths based on user intent (e.g., "automate approvals" vs. "monitor SLAs").
   - Roll out in-app, real-time feedback loops powered by GPT-based agents.
   - Improve load performance by 2x for dashboards with >50 KPIs.

3. **Strengthen Developer & Partner Ecosystem**
   - Release v2 of our SDK with improved documentation, type hints, and example templates.
   - Stand up a community forum with staff AMAs and biweekly contributor highlights.
   - Co-market with 5+ strategic partners via webinars and case studies.

**Execution and Ownership**

To bring these pillars to life, we’re adopting a revised execution framework that emphasizes cross-functional alignment and quarterly delivery milestones. Here's how we're structuring execution:

- **Initiative leads** will own end-to-end delivery of key H2 priorities, with matrixed team support across Product, Eng, Design, and GTM.
- We’ll move to a **6-week build / 2-week cool-down** cadence for product teams, enabling more rapid iteration and stakeholder visibility.
- OKRs will be published by July 7, with team-level commitments finalized by July 14. Expect a company-wide H2 kickoff on July 10.

**Upcoming Milestones**

Here are a few key dates to keep in mind:
- **July 10** – H2 Kickoff All-Hands
- **July 15** – Beta release of Dashboard Builder v3
- **August 5** – Early Access cohort for Auto-Routing Engine
- **September 12** – Partner Summit (virtual + in-person hybrid)
- **October 2** – Internal Hack Week focused on “User Delight” experiments

**Final Thoughts**

It’s easy to get caught up in quarterly metrics and delivery dates, but I want to take a moment to zoom out. We’re building a product that sits at the intersection of intelligence, trust, and usability — something few others are positioned to do. That takes more than smart features or fast sprints; it requires care, craft, and conviction in our users’ success.

I’m grateful for the intensity and creativity you bring to your work every day. Let’s make H2 not just our most productive half yet, but the one that most clearly defines what we stand for as a team.

Please reach out if anything in this note is unclear or sparks ideas — I’d love to hear from you.

Onward,

Alex
Chief Product Officer
"""

            email_text = """
Subject: Q2 Product Strategy Alignment & Upcoming Initiatives

Hi team,

I hope everyone had a restful weekend. I wanted to take a moment to summarize our key strategic focuses for Q2 and align on upcoming initiatives across Product, Engineering, and GTM. This email is long, but please read in full — it outlines several important updates.

First, our **core strategic objective** remains improving user retention and engagement in our mid-market segment. The data from Q1 shows promising early traction, particularly in workflows tied to onboarding and personalized dashboards. However, we still see significant drop-offs after day 7, especially for users in the financial services vertical.

To address this, we’re launching the following initiatives:
- **Segmented onboarding flows** tailored to vertical-specific user types.
- **Behavior-based nudging** to guide users back into the app (led by Growth).
- **Deeper integration of predictive insights** using our new ML model (led by Data & Infra).

In terms of feature development, the **Collaboration Suite** will enter public beta in mid-May. Product specs are finalized, and Engineering has completed 65% of implementation. Key remaining components include comment threading, permissions revamp, and Slack integration. The rollout will follow a gated release to power users in our top 20 accounts.

For GTM, Sales Enablement will begin training next week, with new materials focused on narrative selling around real-time collaboration. Marketing is finalizing collateral with customer stories and competitive differentiation against Asana and ClickUp.

I also want to highlight a cross-functional initiative we're calling **“Trust & Transparency.”** It focuses on surfacing data lineage, audit trails, and admin controls more clearly in the UI. This will be especially important for our enterprise accounts as we pursue ISO-27001 and SOC 2 Type II certification. Design will share early concepts in Friday’s critique.

Lastly, please block time on your calendars for the Q2 kickoff on Thursday at 10am PT. We’ll walk through OKRs, demo early versions of the new workflows, and hear directly from CSMs about user feedback.

Let me know if you have any questions or concerns, and thanks again for your continued hard work. Let’s make Q2 our most impactful quarter yet.

Best,  
Allison
Head of Product
"""
            email_text2 = """
Subject: Weekly Update – Apollo Project Milestones, Risks & Next Steps

Hi all,

Following up on our standing Friday update, I wanted to provide a detailed snapshot of where we stand with the Apollo Project as we close out week 7 of the timeline. Thanks again for everyone's dedication and coordination — the progress this week was substantial, and we’re still tracking toward our targeted mid-August launch.

**1. Development Progress**
The backend migration to the new GraphQL architecture is now 85% complete. We hit a minor snag with schema compatibility in the reporting layer, but a fix is already in QA and should be pushed to staging by Tuesday. Frontend work on the revamped dashboard is ahead of schedule — special shoutout to the Design team for quickly implementing the revised UX flows after stakeholder feedback earlier this week.

**2. Data & Integration**
ETL pipelines are live and successfully ingesting data from 4 out of 6 partner systems. We’re still waiting on final API access from Nova Financial and Zebra CRM; our legal and vendor teams are actively following up. If access isn’t confirmed by Wednesday, we’ll escalate via the integration escalation path outlined in the kickoff doc. No blockers on internal data normalization.

**3. Risk Management**
There are two emerging risks I want to flag:
- **Authentication latency** in the legacy SSO flow is still exceeding 1.5 seconds. A dedicated SWAT team has been formed to isolate the bottleneck, and they’ll report daily starting Monday.
- **Content management tooling** lacks proper version control, which caused a regression last sprint. The Platform team is evaluating CMS alternatives that support multi-environment workflows.

**4. Timeline**
We remain on track for the following:
- Internal MVP demo: August 2nd
- Limited external pilot: August 9th
- Full GA: August 19th

However, these dates are contingent on the above risks being mitigated. I’ll send out a revised Gantt chart early next week to reflect the updated confidence levels by milestone.

**5. Next Steps**
- Engineering will complete code freeze on Phase II modules by Thursday EOD.
- UAT coordination meetings begin Wednesday; invites will go out today.
- Marketing has begun drafting go-to-market messaging based on initial value metrics — please review the proposed positioning by Tuesday so we can finalize for pilot outreach.

As always, thank you for the strong collaboration. Please don’t hesitate to ping me if you have questions, or feel free to drop them in our shared Apollo Slack channel.

Enjoy the weekend,  
Jared  
Project Manager – Apollo
"""
            print(AI_API.summarize_array([long_email, email_text, email_text2]))    


        elif user_input == "test cleaning":
            for gmail in gmail_Objects:
                print("new email! --------------------------------")
                html_content = Gmail_Interface.get_plain_text_body(gmail, 'text/html')
                if html_content:
                    print("Html\n")
                    print(Gmail_Interface.html_clean(html_content))
                else:
                    print("Html\n")
                    print("No HTML content found")
                print("Plain\n")
                plain_content = Gmail_Interface.get_plain_text_body(gmail, 'text/plain')
                if plain_content:
                    print(Gmail_Interface.plain_clean(plain_content))
                else:
                    print("No plain text content found")
                print("--------------------------------\n")
        elif user_input == "test prepend with title":
            for gmail in gmail_Objects:
                print("new email! --------------------------------")
                print(Gmail_Interface.prepend_with_title("Subject", Gmail_Interface.get_subject_from_message(gmail), "Test body"))
                print("--------------------------------\n")
        elif user_input == "test truncate":
            print(f"token count: {AI_API.num_tokens_from_string('This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this.')}")
            print(AI_API.split_text_into_chunks("This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this.", 100))
            print(AI_API.split_text_into_chunks("This is a test of the truncate function It should be able to handle this This is a test of the truncate function It should be able to handle this This is a test of the truncate function It should be able to handle this.", 100))
            print(AI_API.truncate_text_to_tokens("This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this. This is a test of the truncate function. It should be able to handle this.", 100))
        elif user_input == "test summarize emails":
            print(AI_API.summarize_Emails(email_objects))
        elif user_input == "query vector db":
            vector_Response = VectorDB.query_vectorDB_combined(vector_db, "What was the email on one medical about?")
            print(VectorDB.extract_body_text_from_results(vector_Response))
            print(VectorDB.extract_from_address_from_results(vector_Response))
        elif user_input == "I'd like to ask a question about a specific email":
            print("What is the email address that sent the email you're looking for? Type None if you don't know")
            sender = input("> ")

            if sender.strip().lower() == "none":
                sender = None

            print("And what is your question?")
            question = input("> ")
            vector_Response = VectorDB.query_vectorDB_combined(vector_db, question, sender)
            body = VectorDB.extract_body_text_from_results(vector_Response)
            from_address = VectorDB.extract_from_address_from_results(vector_Response)
            output = AI_API.answer_question_with_context(question, from_address, body, 5000)
            print(output)
        elif user_input == "test summarize array":
            email_text = """
Subject: Q2 Product Strategy Alignment & Upcoming Initiatives

Hi team,

I hope everyone had a restful weekend. I wanted to take a moment to summarize our key strategic focuses for Q2 and align on upcoming initiatives across Product, Engineering, and GTM. This email is long, but please read in full — it outlines several important updates.

First, our **core strategic objective** remains improving user retention and engagement in our mid-market segment. The data from Q1 shows promising early traction, particularly in workflows tied to onboarding and personalized dashboards. However, we still see significant drop-offs after day 7, especially for users in the financial services vertical.

To address this, we’re launching the following initiatives:
- **Segmented onboarding flows** tailored to vertical-specific user types.
- **Behavior-based nudging** to guide users back into the app (led by Growth).
- **Deeper integration of predictive insights** using our new ML model (led by Data & Infra).

In terms of feature development, the **Collaboration Suite** will enter public beta in mid-May. Product specs are finalized, and Engineering has completed 65% of implementation. Key remaining components include comment threading, permissions revamp, and Slack integration. The rollout will follow a gated release to power users in our top 20 accounts.

For GTM, Sales Enablement will begin training next week, with new materials focused on narrative selling around real-time collaboration. Marketing is finalizing collateral with customer stories and competitive differentiation against Asana and ClickUp.

I also want to highlight a cross-functional initiative we're calling **“Trust & Transparency.”** It focuses on surfacing data lineage, audit trails, and admin controls more clearly in the UI. This will be especially important for our enterprise accounts as we pursue ISO-27001 and SOC 2 Type II certification. Design will share early concepts in Friday’s critique.

Lastly, please block time on your calendars for the Q2 kickoff on Thursday at 10am PT. We’ll walk through OKRs, demo early versions of the new workflows, and hear directly from CSMs about user feedback.

Let me know if you have any questions or concerns, and thanks again for your continued hard work. Let’s make Q2 our most impactful quarter yet.

Best,  
Allison
Head of Product
"""
            email_text2 = """
Subject: Weekly Update – Apollo Project Milestones, Risks & Next Steps

Hi all,

Following up on our standing Friday update, I wanted to provide a detailed snapshot of where we stand with the Apollo Project as we close out week 7 of the timeline. Thanks again for everyone's dedication and coordination — the progress this week was substantial, and we’re still tracking toward our targeted mid-August launch.

**1. Development Progress**
The backend migration to the new GraphQL architecture is now 85% complete. We hit a minor snag with schema compatibility in the reporting layer, but a fix is already in QA and should be pushed to staging by Tuesday. Frontend work on the revamped dashboard is ahead of schedule — special shoutout to the Design team for quickly implementing the revised UX flows after stakeholder feedback earlier this week.

**2. Data & Integration**
ETL pipelines are live and successfully ingesting data from 4 out of 6 partner systems. We’re still waiting on final API access from Nova Financial and Zebra CRM; our legal and vendor teams are actively following up. If access isn’t confirmed by Wednesday, we’ll escalate via the integration escalation path outlined in the kickoff doc. No blockers on internal data normalization.

**3. Risk Management**
There are two emerging risks I want to flag:
- **Authentication latency** in the legacy SSO flow is still exceeding 1.5 seconds. A dedicated SWAT team has been formed to isolate the bottleneck, and they’ll report daily starting Monday.
- **Content management tooling** lacks proper version control, which caused a regression last sprint. The Platform team is evaluating CMS alternatives that support multi-environment workflows.

**4. Timeline**
We remain on track for the following:
- Internal MVP demo: August 2nd
- Limited external pilot: August 9th
- Full GA: August 19th

However, these dates are contingent on the above risks being mitigated. I’ll send out a revised Gantt chart early next week to reflect the updated confidence levels by milestone.

**5. Next Steps**
- Engineering will complete code freeze on Phase II modules by Thursday EOD.
- UAT coordination meetings begin Wednesday; invites will go out today.
- Marketing has begun drafting go-to-market messaging based on initial value metrics — please review the proposed positioning by Tuesday so we can finalize for pilot outreach.

As always, thank you for the strong collaboration. Please don’t hesitate to ping me if you have questions, or feel free to drop them in our shared Apollo Slack channel.

Enjoy the weekend,  
Jared  
Project Manager – Apollo
"""
            email_text3 = """
Subject: Thank You for a Wonderful Year – Reflections from Room 14

Dear Parents and Guardians,

As we wrap up the school year and prepare to send your children into summer (and for some, into middle school!), I wanted to take a moment to express my sincere gratitude for the partnership, trust, and encouragement you've offered throughout the year. Room 14 has been more than just a classroom—it’s been a community, and I feel incredibly fortunate to have been part of your child’s journey.

This year brought both challenges and triumphs. From navigating hybrid learning in the fall to adjusting to full in-person instruction by winter, our students have shown resilience, adaptability, and compassion. They learned how to collaborate, how to ask big questions, and how to support one another when things didn’t go as planned. These are life skills that go beyond reading logs or math facts, and I hope they carry them forward.

Some highlights from our year:
- Our **Community Garden Project** yielded actual tomatoes and a lot of mud-splattered smiles.
- During **Science Week**, the “Build Your Own Ecosystem” kits were a hit—and yes, some of those moss terrariums are still thriving!
- The **Living History Museum** last month was, frankly, extraordinary. The confidence and poise each student showed while stepping into the shoes of historical figures was inspiring to watch.

I also want to acknowledge the many behind-the-scenes ways you made this year possible. From helping with home reading, to packing lunches, attending parent-teacher conferences, and encouraging your kids when the Wi-Fi dropped during Zoom lessons—you were there. Thank you.

For those moving on to new schools, I wish you and your children all the best. You’ll be missed, and I hope our paths cross again. For returning families, I look forward to seeing you in the hallways next year.

I’ve attached a folder of photos from various events this year (password-protected for privacy), as well as a few resources for summer reading and enrichment if you’re interested. There's no pressure—rest and play are important too!

Wishing you a joyful, restorative summer filled with sunshine, laughter, and books that you can’t put down.

Warmly,  
Ms. Lillian Ortega  
Grade 5 – Room 14
"""
            emails = [email_text, email_text2, email_text3]
            print(AI_API.summarize_text(email_text))
            print(AI_API.summarize_text(email_text2))
            print(AI_API.summarize_text(email_text3))
            print(AI_API.summarize_array(emails))     
            # print(AI_API.summarize_array(emails))     

main()

elif user_input == "get unread emails":
            print(Gmail_Interface.count_unread_emails(service))
            emails = Gmail_Interface.get_unread_emails(service)
            bodytext = []
            for email in emails:
                bodytext.append(Gmail_Interface.get_clean_plain_text_body(email))
            print(bodytext)
            print("neat, huh?")
        elif user_input == "compare html and plain text":
            emails = Gmail_Interface.get_unread_emails(service)
            for email in emails:
                print(Gmail_Interface.html_clean(
                    Gmail_Interface.get_plain_text_body(email, 'text/plain')))
                print(Gmail_Interface.plain_clean(
                    Gmail_Interface.get_plain_text_body(email, 'text/html')))
        elif user_input == "compare token cost of JSON vs. text":
            emails = Gmail_Interface.get_unread_emails(service)
            token_text = 0
            JSON_text = 0
            for email in emails:
               token_text += AI_API.num_tokens_from_string(
                   Gmail_Interface.get_plain_text_body(email, 'text/plain'))
               JSON_text += AI_API.num_tokens_from_string(str(email))
            
            print(f"token version (~half the number) {token_text}")
            print(f"JSON version {JSON_text}")
        elif user_input == "test subjects and from_addresses":
            emails = Gmail_Interface.get_unread_emails(service)
            for email in emails:
                subject = Gmail_Interface.get_subject_from_message(email)
                sender = Gmail_Interface.get_sender_from_message(email)
                print(f"Subject: {subject}")
                print(f"From: {sender}")
                print("---")

'''