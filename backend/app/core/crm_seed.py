import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select
from backend.app.core.database import AsyncSessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.crm import (
    Organization, CRMUser, Team, Company, Contact, Lead, PipelineStage, Opportunity,
    Activity, Task, Campaign, Notification, CRMAuditLog
)

def utc_now():
    return datetime.now(timezone.utc)

async def seed_crm_database():
    """Initializes tables and seeds initial realistic data for The Full Circle."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if organization already exists
        res = await db.execute(select(Organization).where(Organization.slug == "thefullcircle"))
        org = res.scalars().first()
        if org:
            print("The Full Circle CRM database is already seeded.")
            return

        print("Seeding The Full Circle CRM database...")

        # 1. Organization
        org = Organization(
            id="org-thefullcircle",
            name="The Full Circle",
            slug="thefullcircle",
            domain="thefullcircle.in",
            settings={"currency": "INR", "timezone": "Asia/Kolkata", "portal": "login01.liono360.com"}
        )
        db.add(org)
        await db.flush()

        # 2. Teams
        enterprise_team = Team(
            id="team-enterprise",
            org_id=org.id,
            name="Enterprise & Healthcare BDEs",
            description="B2B corporate wellness, campus resilience, and institutional partnerships"
        )
        clinical_team = Team(
            id="team-clinical",
            org_id=org.id,
            name="Clinical & POSH Advisory",
            description="Specialist consultation, POSH compliance, and psychological therapy leads"
        )
        db.add_all([enterprise_team, clinical_team])
        await db.flush()

        # 3. Users with RBAC roles
        users_data = [
            {
                "id": "usr-mritunjay",
                "username": "mritunjay",
                "email": "Mritunjay.Singh@thefullcircle.in",
                "full_name": "Mritunjay Rajesh Singh",
                "first_name": "Mritunjay",
                "last_name": "Singh",
                "role": "SALES_EXECUTIVE",
                "phone": "8767187638",
                "team_id": enterprise_team.id,
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80",
                "quota": 800000.0,
                "won_revenue": 540000.0,
                "active_deals_count": 5,
                "profile_data": {
                    "middleName": "Rajesh",
                    "gender": "Male",
                    "personalEmail": "mritunjay.personal@gmail.com",
                    "phoneNumbers": {
                        "work": "+91 8767187638",
                        "mobile": "+91 8767187638",
                        "home": "+91 22 2890 1122",
                        "other": "+91 99887 76655",
                        "fax": "+91 22 2890 1123"
                    },
                    "communicationPreferences": {
                        "sms": True,
                        "email": True,
                        "call": True
                    }
                }
            },
            {
                "id": "usr-rishi",
                "username": "rishi",
                "email": "rishi.malik@thefullcircle.in",
                "full_name": "Dr. Rishi Malik",
                "first_name": "Rishi",
                "last_name": "Malik",
                "role": "SUPERADMIN",
                "phone": "+91 98112 34567",
                "team_id": clinical_team.id,
                "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80",
                "quota": 1500000.0,
                "won_revenue": 1420000.0,
                "active_deals_count": 8,
            },
            {
                "id": "usr-supriya",
                "username": "supriya",
                "email": "supriya.nair@thefullcircle.in",
                "full_name": "Supriya Nair",
                "first_name": "Supriya",
                "last_name": "Nair",
                "role": "SALES_MANAGER",
                "phone": "+91 98201 56789",
                "team_id": enterprise_team.id,
                "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80",
                "quota": 1200000.0,
                "won_revenue": 1080000.0,
                "active_deals_count": 6,
            },
            {
                "id": "usr-shraddha",
                "username": "shraddha",
                "email": "shraddha.j@thefullcircle.in",
                "full_name": "Shraddha Joshi",
                "first_name": "Shraddha",
                "last_name": "Joshi",
                "role": "SALES_EXECUTIVE",
                "phone": "+91 99304 11223",
                "team_id": enterprise_team.id,
                "avatar": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80",
                "quota": 700000.0,
                "won_revenue": 490000.0,
                "active_deals_count": 4,
            },
            {
                "id": "usr-rahul",
                "username": "rahul",
                "email": "rahul.s@thefullcircle.in",
                "full_name": "Rahul Sharma",
                "first_name": "Rahul",
                "last_name": "Sharma",
                "role": "DATA_RESEARCHER",
                "phone": "+91 98190 33445",
                "team_id": enterprise_team.id,
                "avatar": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop&q=80",
                "quota": 500000.0,
                "won_revenue": 120000.0,
                "active_deals_count": 2,
            },
            {
                "id": "usr-ananya",
                "username": "ananya",
                "email": "ananya.d@thefullcircle.in",
                "full_name": "Ananya Deshmukh",
                "first_name": "Ananya",
                "last_name": "Deshmukh",
                "role": "VIEWER",
                "phone": "+91 98330 66778",
                "team_id": enterprise_team.id,
                "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
                "quota": 0.0,
                "won_revenue": 0.0,
                "active_deals_count": 0,
            }
        ]

        created_users = {}
        for u in users_data:
            user_obj = CRMUser(
                id=u["id"],
                org_id=org.id,
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                hashed_password=get_password_hash("password123"),
                role=u["role"],
                phone=u["phone"],
                team_id=u["team_id"],
                avatar=u["avatar"],
                quota=u["quota"],
                won_revenue=u["won_revenue"],
                active_deals_count=u["active_deals_count"],
                profile_data=u.get("profile_data", {}),
                preferences={
                    "menuType": "Static",
                    "landingPage": "Leads",
                    "inputStyle": "Outlined",
                    "flatLayoutColor": "bg-slate-900",
                    "themeColor": "#2563eb"
                }
            )
            db.add(user_obj)
            created_users[u["id"]] = user_obj

        await db.flush()

        # 4. Pipeline Stages
        stages = [
            PipelineStage(id="stage-disc", org_id=org.id, stage_key="discovery", label="Needs Discovery", probability=25, display_order=1, color="#3b82f6"),
            PipelineStage(id="stage-prop", org_id=org.id, stage_key="proposal", label="Care Plan Proposal", probability=50, display_order=2, color="#8b5cf6"),
            PipelineStage(id="stage-nego", org_id=org.id, stage_key="negotiation", label="Legal & SLA Review", probability=75, display_order=3, color="#f59e0b"),
            PipelineStage(id="stage-won", org_id=org.id, stage_key="won", label="Retainer Won", probability=100, display_order=4, color="#10b981"),
            PipelineStage(id="stage-lost", org_id=org.id, stage_key="lost", label="Unqualified / Lost", probability=0, display_order=5, color="#ef4444"),
        ]
        db.add_all(stages)
        await db.flush()

        # 5. Companies
        comp_zomato = Company(
            id="comp-zomato",
            org_id=org.id,
            name="Zomato Limited",
            website="https://www.zomato.com",
            domain="zomato.com",
            industry="Internet & Food Delivery",
            description="Leading food delivery and restaurant discovery aggregator operating in 500+ Indian cities.",
            hq_location="Gurugram, Haryana",
            city="Gurugram",
            state="Haryana",
            country="India",
            employee_count=4500,
            revenue_range="₹4,000 Cr+",
            founded_year=2008,
            company_type="Enterprise",
            status="Active",
            company_score=94,
            technology_stack=["React", "Python", "Kubernetes", "AWS"],
            social_links={"linkedIn": "https://linkedin.com/company/zomato"}
        )

        comp_cred = Company(
            id="comp-cred",
            org_id=org.id,
            name="Dreamplug Technologies (CRED)",
            website="https://cred.club",
            domain="cred.club",
            industry="Fintech & Digital Payments",
            description="Reward-centric financial services and premium credit card bill payments platform.",
            hq_location="Bengaluru, Karnataka",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            employee_count=1200,
            revenue_range="₹1,500 Cr+",
            founded_year=2018,
            company_type="Enterprise",
            status="Active",
            company_score=92,
            technology_stack=["Next.js", "Go", "Kafka", "AWS"],
            social_links={"linkedIn": "https://linkedin.com/company/cred_club"}
        )

        comp_razorpay = Company(
            id="comp-razorpay",
            org_id=org.id,
            name="Razorpay Software Pvt Ltd",
            website="https://razorpay.com",
            domain="razorpay.com",
            industry="Fintech & Payment Gateway",
            description="Full-stack financial services and payments infrastructure provider powering 10M+ businesses in India.",
            hq_location="Bengaluru, Karnataka",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            employee_count=3200,
            revenue_range="₹2,500 Cr+",
            founded_year=2014,
            company_type="Enterprise",
            status="Active",
            company_score=96,
            technology_stack=["React", "PHP", "Go", "AWS", "Datadog"],
            social_links={"linkedIn": "https://linkedin.com/company/razorpay"}
        )

        comp_max = Company(
            id="comp-max",
            org_id=org.id,
            name="Max Healthcare Institute",
            website="https://www.maxhealthcare.in",
            domain="maxhealthcare.in",
            industry="Healthcare & Hospital Chain",
            description="Leading provider of comprehensive, seamless and integrated healthcare services across 18 hospitals.",
            hq_location="New Delhi, Delhi NCR",
            city="New Delhi",
            state="Delhi",
            country="India",
            employee_count=14000,
            revenue_range="₹5,000 Cr+",
            founded_year=2001,
            company_type="Institution",
            status="Active",
            company_score=88,
            social_links={"linkedIn": "https://linkedin.com/company/max-healthcare"}
        )

        comp_ashoka = Company(
            id="comp-ashoka",
            org_id=org.id,
            name="Ashoka University",
            website="https://www.ashoka.edu.in",
            domain="ashoka.edu.in",
            industry="Higher Education & Research",
            description="Pioneering liberal arts and sciences university focused on holistic student well-being and psychological resilience.",
            hq_location="Sonipat, Haryana",
            city="Sonipat",
            state="Haryana",
            country="India",
            employee_count=1200,
            revenue_range="₹400 Cr+",
            founded_year=2014,
            company_type="Institution",
            status="Active",
            company_score=90,
            social_links={"linkedIn": "https://linkedin.com/school/ashoka-university"}
        )

        db.add_all([comp_zomato, comp_cred, comp_razorpay, comp_max, comp_ashoka])
        await db.flush()

        # 6. Contacts
        contacts = [
            Contact(
                id="cont-akriti-zomato",
                org_id=org.id,
                company_id=comp_zomato.id,
                first_name="Akriti",
                last_name="Gupta",
                full_name="Akriti Gupta",
                designation="VP - People Experience & Total Rewards",
                department="Human Resources",
                email="akriti.gupta@zomato.com",
                phone="+91 98101 22334",
                linkedin_url="https://linkedin.com/in/akriti-gupta-hr",
                location="Gurugram, India",
                seniority="VP",
                is_decision_maker=True
            ),
            Contact(
                id="cont-vikram-cred",
                org_id=org.id,
                company_id=comp_cred.id,
                first_name="Vikram",
                last_name="Mehta",
                full_name="Vikram Mehta",
                designation="Head of People Operations & Culture",
                department="People Operations",
                email="vikram.mehta@cred.club",
                phone="+91 98200 44556",
                linkedin_url="https://linkedin.com/in/vikram-mehta-cred",
                location="Bengaluru, India",
                seniority="Director",
                is_decision_maker=True
            ),
            Contact(
                id="cont-natasha-razorpay",
                org_id=org.id,
                company_id=comp_razorpay.id,
                first_name="Natasha",
                last_name="Sen",
                full_name="Natasha Sen",
                designation="Chief People Officer",
                department="Executive HR",
                email="natasha.sen@razorpay.com",
                phone="+91 98450 77889",
                linkedin_url="https://linkedin.com/in/natashasen-cpo",
                location="Bengaluru, India",
                seniority="C-Level",
                is_decision_maker=True
            ),
            Contact(
                id="cont-sunita-max",
                org_id=org.id,
                company_id=comp_max.id,
                first_name="Dr. Sunita",
                last_name="Kapoor",
                full_name="Dr. Sunita Kapoor",
                designation="Director - Clinical Psychology & Rehabilitation",
                department="Medical Services",
                email="dr.sunita@maxhealthcare.in",
                phone="+91 98110 33445",
                location="New Delhi, India",
                seniority="Director",
                is_decision_maker=True
            ),
            Contact(
                id="cont-arjun-ashoka",
                org_id=org.id,
                company_id=comp_ashoka.id,
                first_name="Prof. Arjun",
                last_name="Vaidya",
                full_name="Prof. Arjun Vaidya",
                designation="Dean of Student Affairs & Mental Health Committee",
                department="Student Affairs",
                email="arjun.vaidya@ashoka.edu.in",
                phone="+91 98180 55667",
                location="Sonipat, Haryana",
                seniority="Director",
                is_decision_maker=True
            )
        ]
        db.add_all(contacts)
        await db.flush()

        # 7. Leads covering all 17 calling dispositions
        dispositions = [
            ("Open Leads", "lead-xitij", "Xitij Parmar", "Parmar Capital & Asset Management", "Managing Partner", "xitij.parmar@parmarcapital.in", "+91 98201 11223", "Mumbai", "Financial Services", 88),
            ("New", "lead-aanchal", "Aanchal Singhania", "Singhania Logistics & Supply Chain", "Chief Human Resources Officer", "aanchal.s@singhanialogistics.in", "+91 98110 44556", "New Delhi", "Logistics & Fleet", 85),
            ("Early Researcher", "lead-varun", "Varun Khandelwal", "Khandelwal Diagnostic Labs", "Managing Director", "varun@khandelwaldiagnostics.com", "+91 98300 77889", "Kolkata", "Diagnostics", 76),
            ("Interested", "lead-tanvi", "Tanvi Bhatia", "Bhatia Global School & Preschools", "Director of Student Well-being & Counseling", "tanvi.bhatia@bhatiaglobal.edu.in", "+91 98720 33445", "Chandigarh", "K-12 Education", 91),
            ("Call Back", "lead-devendra", "Devendra Joshi", "Joshi Agro & Chemicals Ltd", "Vice President - People & Administration", "devendra.j@joshiagro.in", "+91 94250 88990", "Indore", "Manufacturing", 79),
            ("Follow UP", "lead-radhika", "Radhika Kulkarni", "Kulkarni Engineering Works", "Senior Manager - EHS & Employee Welfare", "radhika.k@kulkarniengg.com", "+91 98220 55667", "Pune", "Heavy Engineering", 82),
            ("Not-Intrested", "lead-manish", "Manish Tiwari", "Tiwari Real Estate Developers", "General Manager - Operations", "manish.tiwari@tiwarirealty.in", "+91 98910 22334", "Noida", "Real Estate", 48),
            ("Invalid Number", "lead-pooja", "Pooja Hegde", "Hegde Hospitality & Resorts", "Head of People Experience", "pooja.h@hegderesorts.in", "+91 00000 00000", "Goa", "Hospitality", 32),
            ("Language Barrier", "lead-suresh", "Suresh Naidu", "Naidu Spinning & Textile Mills", "Managing Partner", "suresh@naidutextiles.co.in", "+91 98480 66778", "Coimbatore", "Textiles", 54),
            ("No Is Out Of service", "lead-deepak", "Deepak Verma", "Verma Paper Products", "Executive Director", "deepak.verma@vermapaper.com", "+91 98111 00000", "Meerut", "Packaging", 28),
            ("Not Reachable", "lead-megha", "Megha Shrestha", "Shrestha Pharma Formulations", "HR Business Partner", "megha.s@shresthapharma.in", "+91 98765 43210", "Baddi", "Pharmaceuticals", 68),
            ("Voice mail", "lead-aditya", "Aditya Sen", "Sen Cloud Computing Solutions", "VP - Engineering & Culture", "aditya@sencloud.io", "+91 98310 99887", "Kolkata", "IT & Cloud", 84),
            ("Call Cut", "lead-kiran", "Kiran Desai", "Desai Diamond Exports", "Partner", "kiran@desaiexports.in", "+91 98250 12345", "Surat", "Gems & Jewelry", 60),
            ("Bad Lead", "lead-rohit", "Rohit Malani", "Malani Scrap Traders", "Proprietor", "rohit.m@gmail.com", "+91 98980 11111", "Ahmedabad", "Trading", 18),
            ("Not Contactable After 6 Attempt", "lead-geeta", "Geeta Pillai", "Pillai Ocean Logistics", "HR Lead", "geeta@pillaiocean.com", "+91 98470 55443", "Kochi", "Maritime", 42),
            ("DNP", "lead-sanjay", "Sanjay Rawat", "Rawat Security & Facility Services", "Director", "sanjay@rawatsecurity.in", "+91 98100 99999", "Dehradun", "Facility Management", 25),
            ("Closed", "lead-alok", "Alok Chandra", "Chandra Steel Tubes", "Chief Operating Officer", "alok.chandra@chandrasteel.in", "+91 98390 12345", "Kanpur", "Steel & Metals", 90),
        ]

        leads_to_add = []
        for disp, lid, name, comp, desig, email, phone, city, ind, score in dispositions:
            lead_obj = Lead(
                id=lid,
                org_id=org.id,
                name=name,
                company_name=comp,
                designation=desig,
                email=email,
                phone=phone,
                city=city,
                state="State",
                country="India",
                industry=ind,
                calling_disposition=disp,
                status="Interested" if disp in ["Interested", "Follow UP", "Call Back"] else ("Closed" if disp == "Closed" else "New"),
                priority="High" if score >= 80 else ("Medium" if score >= 60 else "Low"),
                lead_score=score,
                score_reason=f"Target score {score}/100 based on {ind} corporate fit in {city}, {desig} decision-maker relevance, and engagement history.",
                score_breakdown={
                    "companyRelevance": min(100, score + 5),
                    "decisionMakerFit": score,
                    "industryFit": min(100, score + 2),
                    "engagement": 75,
                    "intentSignals": 80,
                    "explanation": f"Qualified as high corporate wellness lead for {comp}."
                },
                assigned_user_id=created_users["usr-mritunjay"].id,
                assigned_user_name=created_users["usr-mritunjay"].full_name,
                next_followup_at=utc_now() + timedelta(days=2) if disp in ["Call Back", "Follow UP", "Interested"] else None,
                last_contacted_at=utc_now() - timedelta(days=1)
            )
            leads_to_add.append(lead_obj)

        db.add_all(leads_to_add)
        await db.flush()

        # 8. Opportunities in ₹ INR
        opportunities = [
            Opportunity(
                id="deal-zomato-eap",
                org_id=org.id,
                company_id=comp_zomato.id,
                contact_id=contacts[0].id,
                title="Zomato 4,500-Employee Mental Wellness & 24/7 Crisis Hotline Retainer",
                company_name=comp_zomato.name,
                contact_name=contacts[0].full_name,
                contact_email=contacts[0].email,
                value=2400000.0, # ₹24 Lakhs
                stage="proposal",
                probability=50,
                expected_close_date=utc_now() + timedelta(days=25),
                priority="High",
                owner_id=created_users["usr-mritunjay"].id,
                owner_name=created_users["usr-mritunjay"].full_name,
                notes_count=4
            ),
            Opportunity(
                id="deal-cred-wellness",
                org_id=org.id,
                company_id=comp_cred.id,
                contact_id=contacts[1].id,
                title="CRED Executive Mental Resilience & Leadership Coaching Cohort",
                company_name=comp_cred.name,
                contact_name=contacts[1].full_name,
                contact_email=contacts[1].email,
                value=1500000.0, # ₹15 Lakhs
                stage="negotiation",
                probability=75,
                expected_close_date=utc_now() + timedelta(days=14),
                priority="High",
                owner_id=created_users["usr-supriya"].id,
                owner_name=created_users["usr-supriya"].full_name,
                notes_count=6
            ),
            Opportunity(
                id="deal-razorpay-posh",
                org_id=org.id,
                company_id=comp_razorpay.id,
                contact_id=contacts[2].id,
                title="Razorpay Pan-India POSH Compliance & Workplace Therapy Mandate",
                company_name=comp_razorpay.name,
                contact_name=contacts[2].full_name,
                contact_email=contacts[2].email,
                value=1800000.0, # ₹18 Lakhs
                stage="discovery",
                probability=25,
                expected_close_date=utc_now() + timedelta(days=40),
                priority="Medium",
                owner_id=created_users["usr-shraddha"].id,
                owner_name=created_users["usr-shraddha"].full_name,
                notes_count=3
            ),
            Opportunity(
                id="deal-max-referral",
                org_id=org.id,
                company_id=comp_max.id,
                contact_id=contacts[3].id,
                title="Max Healthcare Clinical Outpatient Therapy Referral Partnership",
                company_name=comp_max.name,
                contact_name=contacts[3].full_name,
                contact_email=contacts[3].email,
                value=3600000.0, # ₹36 Lakhs
                stage="won",
                probability=100,
                expected_close_date=utc_now() - timedelta(days=10),
                priority="High",
                owner_id=created_users["usr-rishi"].id,
                owner_name=created_users["usr-rishi"].full_name,
                notes_count=8
            )
        ]
        db.add_all(opportunities)
        await db.flush()

        # 9. Tasks & Follow-ups (TODAY, OVERDUE, UPCOMING)
        tasks = [
            Task(
                id="task-today-1",
                org_id=org.id,
                type="call",
                title="Call Tanvi Bhatia (Bhatia Global Schools) for demo setup",
                description="Follow up on student psychological assessment care plan.",
                due_date=utc_now(), # TODAY
                priority="High",
                status="pending",
                assigned_to_id=created_users["usr-mritunjay"].id,
                assigned_to_name=created_users["usr-mritunjay"].full_name,
                lead_id="lead-tanvi",
                lead_name="Tanvi Bhatia",
                company_name="Bhatia Global School"
            ),
            Task(
                id="task-overdue-1",
                org_id=org.id,
                type="email",
                title="Send amended SLA draft to Vikram Mehta (CRED)",
                description="Needs review of psychologist confidentiality clause.",
                due_date=utc_now() - timedelta(days=2), # OVERDUE
                priority="High",
                status="pending",
                assigned_to_id=created_users["usr-supriya"].id,
                assigned_to_name=created_users["usr-supriya"].full_name,
                company_id=comp_cred.id,
                company_name=comp_cred.name
            ),
            Task(
                id="task-upcoming-1",
                org_id=org.id,
                type="meeting",
                title="Final review meeting with Zomato VP of Total Rewards",
                description="Present 4,500-employee rollout plan with Dr. Rishi Malik.",
                due_date=utc_now() + timedelta(days=3), # UPCOMING
                priority="High",
                status="pending",
                assigned_to_id=created_users["usr-mritunjay"].id,
                assigned_to_name=created_users["usr-mritunjay"].full_name,
                company_id=comp_zomato.id,
                company_name=comp_zomato.name
            )
        ]
        db.add_all(tasks)

        # 10. Initial Activities
        activities = [
            Activity(
                id="act-1",
                org_id=org.id,
                entity_type="lead",
                entity_id="lead-tanvi",
                entity_name="Tanvi Bhatia",
                type="call",
                title="Cold call completed with Director of Student Well-being",
                description="Discussion on campus mental resilience and anti-bullying counseling sessions.",
                author_id=created_users["usr-mritunjay"].id,
                author_name=created_users["usr-mritunjay"].full_name,
                timestamp=utc_now() - timedelta(hours=3)
            ),
            Activity(
                id="act-2",
                org_id=org.id,
                entity_type="deal",
                entity_id="deal-zomato-eap",
                entity_name="Zomato Limited",
                type="stage_change",
                title="Opportunity advanced to Care Plan Proposal",
                description="Commercial proposal submitted for 4,500 employees (₹24 Lakhs).",
                author_id=created_users["usr-mritunjay"].id,
                author_name=created_users["usr-mritunjay"].full_name,
                timestamp=utc_now() - timedelta(hours=6)
            ),
            Activity(
                id="act-3",
                org_id=org.id,
                entity_type="general",
                type="import",
                title="Batch lead import completed by Rahul Sharma",
                description="Successfully ingested 50,000 corporate leads with 0 duplicate collisions.",
                author_id=created_users["usr-rahul"].id,
                author_name=created_users["usr-rahul"].full_name,
                timestamp=utc_now() - timedelta(days=1)
            )
        ]
        db.add_all(activities)

        # 11. Initial Campaigns
        campaigns = [
            Campaign(
                id="camp-1",
                org_id=org.id,
                name="Q3 Tech Founders & VP HR Mental Resilience Outreach",
                channel="Email",
                status="Active",
                audience_count=450,
                sent_count=420,
                delivered_count=412,
                opened_count=268,
                clicked_count=134,
                replied_count=52,
                converted_count=14
            ),
            Campaign(
                id="camp-2",
                org_id=org.id,
                name="Pan-India Hospital & Diagnostic Healthcare Partnership Outreach",
                channel="LinkedIn",
                status="Active",
                audience_count=180,
                sent_count=175,
                delivered_count=170,
                opened_count=120,
                clicked_count=78,
                replied_count=36,
                converted_count=9
            ),
            Campaign(
                id="camp-3",
                org_id=org.id,
                name="Higher Education & Universities Student Well-being Drive",
                channel="Calling",
                status="Active",
                audience_count=85,
                sent_count=85,
                delivered_count=82,
                opened_count=70,
                clicked_count=55,
                replied_count=28,
                converted_count=11
            )
        ]
        db.add_all(campaigns)

        # 12. Notifications & Audit Logs
        notif = Notification(
            id="notif-welcome",
            org_id=org.id,
            user_id=created_users["usr-mritunjay"].id,
            title="Welcome to The Full Circle Enterprise CRM",
            message="Your account is configured as Sales Executive (BDE) with ₹8.0L retainer quota.",
            type="system"
        )
        audit = CRMAuditLog(
            id="audit-init",
            org_id=org.id,
            user_id=created_users["usr-rishi"].id,
            user_name=created_users["usr-rishi"].full_name,
            action="CREATE",
            entity="Organization",
            entity_id=org.id,
            new_values={"name": org.name, "domain": org.domain},
            ip_address="127.0.0.1"
        )
        db.add_all([notif, audit])

        await db.commit()
        print("The Full Circle CRM database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_crm_database())
