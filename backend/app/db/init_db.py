import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.models import (
    Exam,
    ExamAssignment,
    ExamStatus,
    Question,
    QuestionOption,
    User,
    UserRole,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db() -> None:
    logger.info("Initializing database schema and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Safe idempotent column migrations for existing databases
        from sqlalchemy import text
        migration_statements = [
            "ALTER TABLE exam_attempts ADD COLUMN violation_count INTEGER DEFAULT 0 NOT NULL",
            "ALTER TABLE exam_attempts ADD COLUMN termination_reason VARCHAR(500)",
            "ALTER TABLE exam_attempts ADD COLUMN terminated_at TIMESTAMPTZ",
            "ALTER TABLE exam_attempts ADD COLUMN accepted_rules BOOLEAN DEFAULT TRUE NOT NULL",
            "ALTER TABLE student_answers ADD COLUMN is_marked_for_review BOOLEAN DEFAULT FALSE NOT NULL",
        ]
        for stmt in migration_statements:
            try:
                await conn.execute(text(stmt))
            except Exception:
                # Column already exists or dialect specific handling
                pass
    logger.info("Tables created and schema migrations checked successfully.")

    async with AsyncSessionLocal() as session:
        # 1. Seed Administrator
        res = await session.execute(select(User).where(User.email == "admin@secureexam.edu"))
        admin = res.scalars().first()
        if not admin:
            admin = User(
                email="admin@secureexam.edu",
                hashed_password=get_password_hash("AdminPass123!@#"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(admin)

        # 2. Seed Faculty Members (3 Faculty)
        faculty_data = [
            ("faculty@secureexam.edu", "Prof. Alan Turing", "FacultyPass123!@#"),
            ("grace.hopper@secureexam.edu", "Prof. Grace Hopper", "FacultyPass123!@#"),
            ("donald.knuth@secureexam.edu", "Prof. Donald Knuth", "FacultyPass123!@#"),
        ]
        faculty_users = {}
        for email, name, pwd in faculty_data:
            res = await session.execute(select(User).where(User.email == email))
            u = res.scalars().first()
            if not u:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=UserRole.FACULTY,
                    is_active=True,
                )
                session.add(u)
                await session.flush()
            faculty_users[email] = u

        # 3. Seed Students (4 Students)
        student_data = [
            ("student@secureexam.edu", "Ada Lovelace", "StudentPass123!@#"),
            ("claude.shannon@secureexam.edu", "Claude Shannon", "StudentPass123!@#"),
            ("margaret.hamilton@secureexam.edu", "Margaret Hamilton", "StudentPass123!@#"),
            ("john.neumann@secureexam.edu", "John von Neumann", "StudentPass123!@#"),
        ]
        student_users = {}
        for email, name, pwd in student_data:
            res = await session.execute(select(User).where(User.email == email))
            u = res.scalars().first()
            if not u:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=UserRole.STUDENT,
                    is_active=True,
                )
                session.add(u)
                await session.flush()
            student_users[email] = u

        await session.commit()

        # 4. Seed Exams with Questions & Options
        exams_specs = [
            {
                "title": "CS301: Cryptography & Network Security",
                "description": "Comprehensive assessment on public-key cryptosystems, AES, hashing algorithms, and zero-knowledge proofs.",
                "creator": faculty_users["faculty@secureexam.edu"],
                "duration": 45,
                "total_marks": 20.0,
                "passing_marks": 10.0,
                "negative_marking": True,
                "assigned_students": [
                    student_users["student@secureexam.edu"],
                    student_users["claude.shannon@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "Which mathematical problem provides the computational hardness guarantee for the RSA cryptosystem?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "RSA relies on the integer factorization problem of large composite numbers.",
                        "options": [
                            ("Integer Factorization", True),
                            ("Discrete Logarithm Problem", False),
                            ("Elliptic Curve Point Multiplication", False),
                            ("Traveling Salesperson Problem", False),
                        ],
                    },
                    {
                        "text": "What is the standard block size of the Advanced Encryption Standard (AES)?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "AES operates on a fixed block size of 128 bits regardless of key length.",
                        "options": [
                            ("64 bits", False),
                            ("128 bits", True),
                            ("192 bits", False),
                            ("256 bits", False),
                        ],
                    },
                    {
                        "text": "Which hash function family is standardized in FIPS 202 using the Keccak sponge construction?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "SHA-3 is standardized using the Keccak permutation sponge construction.",
                        "options": [
                            ("MD5", False),
                            ("SHA-1", False),
                            ("SHA-2", False),
                            ("SHA-3", True),
                        ],
                    },
                    {
                        "text": "In a Diffie-Hellman key exchange, what is transmitted over the unencrypted network channel?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "Public values g^a mod p and g^b mod p are transmitted, while secrets a and b remain confidential.",
                        "options": [
                            ("The shared symmetric session key", False),
                            ("Public parameters and computed public values", True),
                            ("The private exponents a and b", False),
                            ("The encrypted plaintext payload", False),
                        ],
                    },
                ],
            },
            {
                "title": "CS302: Advanced Operating Systems & Memory Safety",
                "description": "Kernel architecture, virtual memory management, page replacement algorithms, and memory safety models.",
                "creator": faculty_users["faculty@secureexam.edu"],
                "duration": 30,
                "total_marks": 15.0,
                "passing_marks": 8.0,
                "negative_marking": False,
                "assigned_students": [
                    student_users["student@secureexam.edu"],
                    student_users["john.neumann@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "What hardware structure caches virtual-to-physical address translations in the CPU?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Translation Lookaside Buffer (TLB) caches virtual memory address translations.",
                        "options": [
                            ("Translation Lookaside Buffer (TLB)", True),
                            ("Instruction Register", False),
                            ("Memory Management Unit ROM", False),
                            ("Disk Cache", False),
                        ],
                    },
                    {
                        "text": "Which condition is NOT required for a deadlock state according to Coffman's conditions?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Preemption PREVENTS deadlock; No-preemption is the required Coffman condition.",
                        "options": [
                            ("Mutual Exclusion", False),
                            ("Hold and Wait", False),
                            ("Preemption Allowed", True),
                            ("Circular Wait", False),
                        ],
                    },
                    {
                        "text": "What defense mechanism randomizes memory addresses of the stack, heap, and libraries?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Address Space Layout Randomization (ASLR) obfuscates memory locations against exploit payloads.",
                        "options": [
                            ("Data Execution Prevention (DEP)", False),
                            ("Address Space Layout Randomization (ASLR)", True),
                            ("Stack Canaries", False),
                            ("Control Flow Guard", False),
                        ],
                    },
                ],
            },
            {
                "title": "CS401: Compiler Design & Static Program Analysis",
                "description": "Lexical analysis, LR/LL parsing, intermediate representation (SSA form), data-flow analysis, and optimization.",
                "creator": faculty_users["grace.hopper@secureexam.edu"],
                "duration": 40,
                "total_marks": 20.0,
                "passing_marks": 10.0,
                "negative_marking": False,
                "assigned_students": [
                    student_users["margaret.hamilton@secureexam.edu"],
                    student_users["john.neumann@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "Which intermediate representation property ensures every variable is assigned exactly once?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Static Single Assignment (SSA) form requires every variable to be assigned exactly once.",
                        "options": [
                            ("Static Single Assignment (SSA)", True),
                            ("Three-Address Code (TAC)", False),
                            ("Abstract Syntax Tree (AST)", False),
                            ("Control Flow Graph (CFG)", False),
                        ],
                    },
                    {
                        "text": "What type of grammar can be parsed deterministically by an LR(1) parser?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "LR(1) parsers handle deterministic context-free grammars with 1 lookahead token.",
                        "options": [
                            ("Unrestricted Grammar", False),
                            ("Context-Sensitive Grammar", False),
                            ("Deterministic Context-Free Grammar", True),
                            ("Ambiguous Regular Grammar", False),
                        ],
                    },
                    {
                        "text": "What data-flow analysis framework determines whether a variable may be read before being redefined?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Liveness analysis determines if variable values will be used along future execution paths.",
                        "options": [
                            ("Available Expressions", False),
                            ("Reaching Definitions", False),
                            ("Live Variables Analysis", True),
                            ("Constant Propagation", False),
                        ],
                    },
                    {
                        "text": "Which phase of a modern optimizing compiler removes dead stores and unreachable basic blocks?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Dead code elimination discards operations whose results do not affect observable program behavior.",
                        "options": [
                            ("Lexical Analyzer", False),
                            ("Dead Code Elimination (DCE)", True),
                            ("Register Allocator", False),
                            ("Target Code Assembler", False),
                        ],
                    },
                ],
            },
            {
                "title": "CS402: Software Verification & Formal Methods",
                "description": "Model checking, Hoare logic, loop invariants, axiomatic semantics, and automated theorem proving.",
                "creator": faculty_users["grace.hopper@secureexam.edu"],
                "duration": 35,
                "total_marks": 15.0,
                "passing_marks": 7.0,
                "negative_marking": True,
                "assigned_students": [
                    student_users["student@secureexam.edu"],
                    student_users["margaret.hamilton@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "In Hoare logic, what notation represents the precondition P, program code C, and postcondition Q?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "A Hoare triple is denoted as {P} C {Q}.",
                        "options": [
                            ("{P} C {Q}", True),
                            ("P -> C -> Q", False),
                            ("[P] (C) [Q]", False),
                            ("<P, C, Q>", False),
                        ],
                    },
                    {
                        "text": "What condition must a valid loop invariant satisfy upon entry to the loop?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "A loop invariant must hold true before the first iteration begins.",
                        "options": [
                            ("It must be false until termination", False),
                            ("It must hold true prior to the first iteration", True),
                            ("It must evaluate to the loop counter variable", False),
                            ("It must invert after every odd iteration", False),
                        ],
                    },
                    {
                        "text": "Which temporal logic operator represents 'always in the future' in Linear Temporal Logic (LTL)?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "The G (Globally) operator specifies that a property holds at all points in the future.",
                        "options": [
                            ("X (Next)", False),
                            ("F (Finally)", False),
                            ("G (Globally)", True),
                            ("U (Until)", False),
                        ],
                    },
                ],
            },
            {
                "title": "CS501: Advanced Analysis of Algorithms",
                "description": "Amortized analysis, randomized algorithms, graph flow networks, and NP-completeness reductions.",
                "creator": faculty_users["donald.knuth@secureexam.edu"],
                "duration": 60,
                "total_marks": 25.0,
                "passing_marks": 12.0,
                "negative_marking": True,
                "assigned_students": [
                    student_users["claude.shannon@secureexam.edu"],
                    student_users["john.neumann@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "What is the amortized cost per push/pop operation on a dynamic doubling array?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "While resizing costs O(N), the amortized cost per operation is O(1).",
                        "options": [
                            ("O(1)", True),
                            ("O(log N)", False),
                            ("O(N)", False),
                            ("O(N^2)", False),
                        ],
                    },
                    {
                        "text": "Which algorithm computes maximum flow in a network with time complexity O(V * E^2)?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "The Edmonds-Karp algorithm uses BFS to achieve O(V * E^2) time complexity.",
                        "options": [
                            ("Ford-Fulkerson (DFS)", False),
                            ("Edmonds-Karp", True),
                            ("Dijkstra's Algorithm", False),
                            ("Prim's Algorithm", False),
                        ],
                    },
                    {
                        "text": "What is the expected runtime of randomized QuickSelect to find the k-th smallest element?",
                        "marks": 5.0,
                        "negative_marks": 1.25,
                        "explanation": "Randomized QuickSelect runs in expected linear time O(N).",
                        "options": [
                            ("O(log N)", False),
                            ("O(N)", True),
                            ("O(N log N)", False),
                            ("O(N^2)", False),
                        ],
                    },
                    {
                        "text": "Which fundamental problem was proven NP-complete by Stephen Cook in 1971?",
                        "marks": 10.0,
                        "negative_marks": 2.5,
                        "explanation": "The Cook-Levin theorem established that Boolean Satisfiability (SAT) is NP-complete.",
                        "options": [
                            ("Boolean Satisfiability (SAT)", True),
                            ("Traveling Salesperson Problem", False),
                            ("Graph Coloring", False),
                            ("Vertex Cover", False),
                        ],
                    },
                ],
            },
            {
                "title": "CS502: Computational Complexity & Automata Theory",
                "description": "Turing machine decidability, Rice's theorem, diagonalization, P vs NP, and space complexity classes.",
                "creator": faculty_users["donald.knuth@secureexam.edu"],
                "duration": 45,
                "total_marks": 20.0,
                "passing_marks": 10.0,
                "negative_marking": False,
                "assigned_students": [
                    student_users["claude.shannon@secureexam.edu"],
                    student_users["margaret.hamilton@secureexam.edu"],
                ],
                "questions": [
                    {
                        "text": "According to Rice's Theorem, which properties of Turing machines are undecidable?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "Rice's theorem states any non-trivial semantic property of the language recognized by a TM is undecidable.",
                        "options": [
                            ("All non-trivial semantic properties", True),
                            ("Only whether the machine halts on empty input", False),
                            ("Syntactic state count properties", False),
                            ("Number of tape heads used", False),
                        ],
                    },
                    {
                        "text": "What complexity class contains decision problems solvable by a deterministic Turing machine in polynomial space?",
                        "marks": 5.0,
                        "negative_marks": 0.0,
                        "explanation": "PSPACE is the set of all decision problems that can be solved by a Turing machine using polynomial space.",
                        "options": [
                            ("P", False),
                            ("NP", False),
                            ("PSPACE", True),
                            ("EXPTIME", False),
                        ],
                    },
                    {
                        "text": "What proof technique was developed by Georg Cantor and used by Alan Turing to prove the Halting Problem undecidable?",
                        "marks": 10.0,
                        "negative_marks": 0.0,
                        "explanation": "Cantor's diagonalization argument was adapted by Turing to demonstrate the impossibility of a universal halting decider.",
                        "options": [
                            ("Mathematical Induction", False),
                            ("Diagonalization Argument", True),
                            ("Pigeonhole Principle", False),
                            ("Floyd-Warshall Relaxation", False),
                        ],
                    },
                ],
            },
        ]

        now = datetime.now(UTC)
        for spec in exams_specs:
            res = await session.execute(select(Exam).where(Exam.title == spec["title"]))
            exam = res.scalars().first()
            if not exam:
                exam = Exam(
                    title=spec["title"],
                    description=spec["description"],
                    duration_minutes=spec["duration"],
                    total_marks=spec["total_marks"],
                    passing_marks=spec["passing_marks"],
                    enable_negative_marking=spec["negative_marking"],
                    status=ExamStatus.PUBLISHED,
                    created_by=spec["creator"].id,
                    start_time=now - timedelta(days=1),
                    end_time=now + timedelta(days=30),
                )
                session.add(exam)
                await session.flush()

                # Add Questions
                for q_idx, q_data in enumerate(spec["questions"], start=1):
                    q = Question(
                        exam_id=exam.id,
                        question_text=q_data["text"],
                        marks=q_data["marks"],
                        negative_marks=q_data["negative_marks"],
                        explanation=q_data["explanation"],
                        order_index=q_idx,
                    )
                    session.add(q)
                    await session.flush()

                    for opt_idx, (opt_text, is_corr) in enumerate(q_data["options"], start=1):
                        opt = QuestionOption(
                            question_id=q.id,
                            option_text=opt_text,
                            is_correct=is_corr,
                            order_index=opt_idx,
                        )
                        session.add(opt)

                # Add Student Assignments
                for student in spec["assigned_students"]:
                    assignment = ExamAssignment(
                        exam_id=exam.id,
                        student_id=student.id,
                    )
                    session.add(assignment)

        await session.commit()
        logger.info("Database seeding completed with 3 faculty, 4 students, 6 published exams, and assignments.")


if __name__ == "__main__":
    asyncio.run(init_db())
