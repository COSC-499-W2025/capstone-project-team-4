import re
import os
from collections import defaultdict

# --------------------------------------------------------------------------
# TEST OVERVIEW: MULTI-SKILL JAVA EXTRACTOR
# --------------------------------------------------------------------------
# PURPOSE: Extract and quantify proficiency across 20 distinct Java skills
#          and calculate a density score per 100 LOC.
#
# METHOD: Uses highly specific regular expression patterns to match core
#         constructs, APIs, and annotations associated with each skill category.
#         The detailed list of identifiers found is moved to an appendix for
#         a cleaner main report.
#
# DENSITY SCORE USAGE: The density score (raw_count / LOC * 100) measures the
#                      concentration of a skill's identifiers per 100 lines of
#                      code. This is crucial because it normalizes the score,
#                      preventing long, simple files from scoring higher than
#                      short, complex files. A high density score indicates that
#                      the developer intensely utilized that specific skill
#                      within the analyzed code segment.
# --------------------------------------------------------------------------

# --- 1. Define the Comprehensive Skill Mapping (Code-Focused Identifiers) ---
SKILL_MAPPING = {
    # ----------------------------------------------------------------
    # FOUNDATIONAL SKILLS
    # ----------------------------------------------------------------
    "Object-Oriented Programming (OOP)": [
        r'class\s+[\w$]+', r'new\s+[\w$]+', r'this\.', r'\bprivate\b', 
        r'\bprotected\b', r'\bpublic\b', r'\bextends\b', r'\bimplements\b', 
        r'interface\s+[\w$]+', r'abstract\s+class', r'@Override\b', 
        r'\bsuper\b', r'\binstanceof\b', r'enum\s+[\w$]+', r'final\s+class'
    ],
    "Concurrency & Multithreading": [
        r'new\s+Thread\s*\(', r'implements\s+Runnable\b', r'implements\s+Callable<', 
        r'ExecutorService\s+executor\s*=', r'Future<', r'\bsynchronized\s*\(', 
        r'\bvolatile\s+', r'ReentrantLock', r'lock\.lock\s*\(', r'lock\.unlock\s*\(', 
        r'\bwait\s*\(', r'\bnotify\s*\(', r'\bjoin\s*\(', r'ScheduledExecutorService', r'AtomicInteger'
    ],
    "Exception Handling & Robustness": [
        r'\btry\s*{', r'catch\s*\([\w$]*Exception\s+e\)', r'\bfinally\s*{', 
        r'throw\s+new\s+[\w$]+Exception', r'throws\s+[\w$]+Exception', 
        r'try\s*\([\w\s$]+=.*\)\s*{', r'Logger\s+logger\s*=', r'logger\.error\s*\('
    ],
    "Unit Testing & TDD": [
        r'@Test\b', r'@BeforeEach\b', r'@AfterAll\b', r'Assertions\.assertEquals\s*\(', 
        r'assertThrows\s*\(', r'@Mock\b', r'@InjectMocks\b', r'Mockito\.when\s*\(', r'Mockito\.verify\s*\('
    ],
    # ----------------------------------------------------------------
    # COLLECTIONS & ALGORITHMS
    # ----------------------------------------------------------------
    "Data Structures & Algorithms": [
        r'new\s+ArrayList\s*<', r'HashMap\s*<', r'HashSet\s*<', r'TreeMap\s*<', 
        r'PriorityQueue\s*<', r'Collections\.sort\s*\(', r'Arrays\.sort\s*\(', 
        r'implements\s+Comparable<', r'Comparator\.comparing\s*\('
    ],
    "Functional Programming (Streams)": [
        r'\.stream\s*\(', r'\.map\s*\(', r'\.filter\s*\(', r'\.reduce\s*\(', 
        r'\.collect\s*\(', r'Optional\.of\s*\(', r'Optional\.empty\s*\(', 
        r'->', r'::'
    ],
    "String Manipulation": [
        r'charAt\s*\(', r'substring\s*\(', r'indexOf\s*\(', r'lastIndexOf\s*\(', 
        r'length\s*\(', r'equals\s*\(', r'equalsIgnoreCase\s*\(', r'startsWith\s*\(', 
        r'endsWith\s*\(', r'split\s*\(', r'trim\s*\(', r'concat\s*\(', r'StringBuilder', r'StringBuffer'
    ],
    # ----------------------------------------------------------------
    # APPLICATION/ENTERPRISE SKILLS
    # ----------------------------------------------------------------
    "RESTful API Development": [
        r'@RestController\b', r'@Controller\b', r'@GetMapping\s*\(', r'@PostMapping\s*\(', 
        r'@PutMapping\b', r'@DeleteMapping\b', r'@RequestBody\b', r'@PathVariable\s*\(', 
        r'ResponseEntity\.ok\s*\(', r'ResponseEntity\.status\s*\('
    ],
    "Dependency Injection & IoC": [
        r'@Autowired\b', r'@Inject\b', r'@Component\b', r'@Service\b', r'@Repository\b', 
        r'@Configuration\b', r'@Bean\b', r'@Qualifier\s*\(', r'@Scope\s*\('
    ],
    "Data Persistence & ORM": [
        r'@Entity\b', r'@Id\b', r'@GeneratedValue\s*\(', r'@Column\s*\(', r'@OneToMany\s*\(', 
        r'@ManyToOne\s*\(', r'@JoinColumn\s*\(', r'@Transactional\b', r'entityManager\.persist\s*\(', 
        r'repository\.save\s*\('
    ],
    "File I/O & Serialization": [
        r'new\s+File\s*\(', r'FileInputStream\s+fis\s*=', r'BufferedReader\s+br\s*=', 
        r'Files\.readAllLines\s*\(', r'ObjectOutputStream\s+oos\s*=', r'implements\s+Serializable\b'
    ],
    "Networking (Sockets)": [
        r'Socket\s+socket\s*=', r'ServerSocket\s+server\s*=', r'DatagramSocket\s+ds\s*=', 
        r'DatagramPacket\s+packet\s*=', r'InetAddress\.getByName\s*\('
    ],
    "Logging & Monitoring": [
        r'import\s+org\.slf4j\.Logger', r'LoggerFactory\.getLogger\s*\(', 
        r'logger\.info\s*\(', r'logger\.debug\s*\(', r'logger\.error\s*\('
    ],
    "Security & Crypto": [
        r'@PreAuthorize\s*\(', r'@EnableWebSecurity\b', r'BCryptPasswordEncoder\s*=', 
        r'Cipher\.getInstance\s*\(', r'MessageDigest\.getInstance\s*\('
    ],
    # ----------------------------------------------------------------
    # ARCHITECTURE
    # ----------------------------------------------------------------
    "GUI Development": [
        r'new\s+JFrame\s*\(', r'JPanel\s+panel\s*=', r'JButton\s+btn\s*=', 
        r'addActionListener\s*\(', r'extends\s+Application\b', r'@FXML\b', r'start\s*\(Stage\s+stage\)'
    ],
    "Design Patterns": [
        r'private\s+static\s+Instance\s+inst', r'private\s+MyClass\s*\(\)\s*{}', 
        r'new\s+Builder\s*\(\)\.set[\w$]*\s*\(\)\.build\s*\(', r'Factory\.create\s*\(', 
        r'addListener\s*\(', r'context\.setStrategy\s*\('
    ],
    "CI/CD & Deployment Automation": [
        r'\.github/workflows', r'mvn\s+-DskipTests\s+package', r'\./gradlew\s+build', 
        r'Dockerfile', r'FROM\s+openjdk:17', r'Jenkinsfile'
    ],
    "CLI / Utility": [
        r'public\s+static\s+void\s+main\s*\(String\[\]\s+args\)', r'System\.out\.println\s*\(', 
        r'Scanner\s+sc\s*=\s*new\s+Scanner\s*\(System\.in\)'
    ],
    "Memory & Runtime Awareness": [
        r'System\.gc\s*\(', r'ThreadLocal\s*<', r'WeakReference\s*<', 
        r'SoftReference\s*<', r'protected\s+void\s+finalize\s*\(', r'Runtime\.getRuntime\s*\(\)\.freeMemory'
    ],
    "Android (mobile)": [
        r'extends\s+Activity\b', r'extends\s+Fragment\b', r'Intent\s+intent\s*=', 
        r'Bundle\s+bundle\s*=', r'RecyclerView\b', r'ViewModel\b', r'LiveData\b', r'implements\s+Parcelable\b'
    ],
}

def analyze_java_project(file_path):
    """
    Analyzes a single Java file for all 20 skills based on keyword frequency.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            java_code = f.read()
    except Exception as e:
        return {"error": f"Error reading file: {e}"}

    # Pre-process: Remove comments and standardize whitespace
    code_cleaned = re.sub(r'//.*|\/\*[\s\S]*?\*\/', '', java_code)
    code_lines = java_code.splitlines()
    loc = len(code_lines)
    
    # Calculate score for each skill
    skill_scores = defaultdict(lambda: {"raw_count": 0, "identifier_list": []})
    
    for skill, patterns in SKILL_MAPPING.items():
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, code_cleaned)
            match_count = len(matches)
            count += match_count
            
            if match_count > 0:
                # Store the identifier and its count for the appendix
                skill_scores[skill]["identifier_list"].append(f"'{pattern}' ({match_count})")

        skill_scores[skill]["raw_count"] = count
        # Normalize score by LOC for density (avoid division by zero)
        skill_scores[skill]["density_score"] = round(count / loc * 100, 4) if loc > 0 else 0

    return {
        "total_lines_of_code": loc,
        "skill_scores": skill_scores
    }

def print_analysis_report(analysis_data, project_name="Java Project"):
    """Prints the structured report with appendix to the terminal."""
    if "error" in analysis_data:
        print(f"REPORT ERROR: {analysis_data['error']}")
        return

    print(f"Skill Analysis Report: {project_name}")
    print("---")
    print(f"Lines of Code (LOC): {analysis_data['total_lines_of_code']}")
    print("\nSkill Breakdown by Code Density")
    
    # Sort by Density Score (highest first)
    sorted_skills = sorted(analysis_data['skill_scores'].items(),
                            key=lambda item: item[1]['density_score'], reverse=True)
    
    # --- MAIN REPORT TABLE ---
    print("\n| Skill | Total Matches | Density Score (per 100 LOC) |")

    appendix_data = []

    for skill, scores in sorted_skills:
        if scores["raw_count"] > 0:
            print(f"| {skill} | {scores['raw_count']} | {scores['density_score']} |")
            
            # Populate Appendix data
            appendix_data.append(
                (skill, ", ".join(scores["identifier_list"]))
            )

    # --- APPENDIX ---
    if appendix_data:
        print("\n---")
        print("Appendix: Key Identifiers Found")
        print("The following code fragments were detected to infer the skills listed above.")
        
        print("\n| Skill | Detected Identifiers (Pattern and Count) |")
        for skill, identifiers in appendix_data:
            print(f"| {skill} | {identifiers} |")

# --- 5. Execution Block ---
if __name__ == "__main__":
    # --- DUMMY FILE SETUP ---
    DUMMY_JAVA_CONTENT = """
    // File: StudentProjectMain.java
    import java.io.*;
    import java.util.*;
    import java.util.concurrent.*;
    import org.junit.jupiter.api.Test;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;

    // --- Core OOP ---
    @Component // DI
    public final class TaskManager extends Thread implements Runnable, AutoCloseable {
        
        private final Logger logger = LoggerFactory.getLogger(TaskManager.class);
        private AtomicInteger taskCounter = new AtomicInteger(0); // Concurrency
        private Map<Integer, Future<String>> submittedTasks = new HashMap<>(); // DSA

        @Autowired
        private DataRepository repository; // DI/ORM

        public TaskManager() {
            super();
        }

        @Override // OOP
        public void run() {
            try {
                // Exception Handling
                throw new IllegalStateException("Task running"); 
            } catch (Exception e) {
                logger.error("Error in thread: {}", e.getMessage(), e); // Logging
            }
        }
        
        // --- RESTful/DI Simulation ---
        @Service
        @Transactional 
        public void process(int id) {
                repository.save(new MyEntity());
        }

        // --- Concurrency ---
        public void submitTask(Callable<String> callable) {
            ExecutorService executor = Executors.newFixedThreadPool(4);
            Future<String> future = executor.submit(callable);
            this.submittedTasks.put(taskCounter.incrementAndGet(), future);
        }

        // --- Functional Programming ---
        public List<String> filterTasks(List<String> rawData) {
            return rawData.stream()
                .filter(s -> s.length() > 5) // Streams/FP
                .collect(Collectors.toList());
        }

        // --- File I/O ---
        public void readFile(String path) throws IOException {
                try (FileInputStream fis = new FileInputStream(new File(path))) {
                    // Reading logic here
                }
        }
        
        // --- Unit Testing (Simulated Test File) ---
        @Test
        void testTaskCounter() {
            Assertions.assertEquals(0, taskCounter.get());
        }
    }
    
    interface TaskLifecycle {}
    enum TaskStatus { PENDING, RUNNING }
    """
    DUMMY_FILE_PATH = "MultiSkillProject.java"
    
    # Write the content to a temporary file
    with open(DUMMY_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(DUMMY_JAVA_CONTENT)
        
    # --- Run the analysis ---
    analysis_results = analyze_java_project(DUMMY_FILE_PATH)
    print_analysis_report(analysis_results, project_name="University Final Project")
    
    # --- Cleanup ---
    os.remove(DUMMY_FILE_PATH)