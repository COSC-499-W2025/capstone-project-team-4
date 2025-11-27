# Skill Identifier Mapping

This file is a structural mapping of skills with code identifiers for individual programming languages & frameworks.
---

# Languages

## Java
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Object-Oriented Programming (OOP) | `class MyClass {}`, `public class MyClass`, `new MyClass()`, `this.field`, `private`, `protected`, `public`, `extends BaseClass`, `implements Interface`, `interface InterfaceName {}`, `abstract class AbstractName {}`, `@Override`, `super(...)`, `instanceof`, `enum Colors {}`, `final class` | Core language constructs for classes, inheritance, interfaces, polymorphism, encapsulation. |
| Concurrency & Multithreading | `new Thread(runnable).start()`, `class X implements Runnable`, `class X implements Callable<T>`, `ExecutorService executor = Executors.newFixedThreadPool(n)`, `Future<T> f = executor.submit(callable)`, `synchronized(this) {}`, `volatile int count;`, `ReentrantLock lock = new ReentrantLock()`, `lock.lock()`, `lock.unlock()`, `wait()`, `notify()`, `notifyAll()`, `thread.join()`, `ScheduledExecutorService`, `AtomicInteger` | Actual concurrency APIs and keywords used for parallelism and synchronization. |
| Exception Handling & Robustness   | `try { } catch (IOException e) { } finally { }`, `throw new IOException("msg")`, `throws IOException`, `try (Resource r = ...) {}`, `Logger logger = LoggerFactory.getLogger(...)`, `logger.error(...)`, `@ExceptionHandler(Exception.class)` | Java exception model and logging usage indicating robust error handling. |
| Unit Testing & TDD | `@Test`, `@BeforeEach`, `@AfterAll`, `Assertions.assertEquals(expected, actual)`, `assertThrows(...)`, `@Mock`, `@InjectMocks`, `Mockito.when(obj.method()).thenReturn(...)`, `Mockito.verify(mock).method() | JUnit & Mockito identifiers used in unit tests.                                             |
| RESTful API Development | `@RestController`, `@Controller`, `@GetMapping("/foo")`, `@PostMapping("/foo")`, `@PutMapping`, `@DeleteMapping`, `@RequestBody`, `@PathVariable("id")`, `ResponseEntity.ok()`, `ResponseEntity.status(HttpStatus.CREATED)`| Spring MVC / Spring Boot REST endpoint annotations and response objects.|
| Dependency Injection & IoC | `@Autowired`, `@Inject`, `@Component`, `@Service`, `@Repository`, `@Configuration`, `@Bean`, `@Qualifier("name")`, `@Scope("prototype") | Spring-style DI annotations and bean configuration patterns.|
| Functional Programming (Streams)  | `list.stream()`, `.map(x -> x.foo())`, `.filter(x -> x>0)`, `.reduce(0, Integer::sum)`, `.collect(Collectors.toList())`, `Optional.of(value)`, `Optional.empty()`, `ClassName::methodName` | Java 8+ stream & Optional usage evidencing FP style.|
| Data Persistence & ORM | `@Entity`, `@Id`, `@GeneratedValue(strategy = ...)`, `@Column(name = "col")`, `@OneToMany(mappedBy="")`, `@ManyToOne`, `@JoinColumn(name="fk")`, `@Transactional`, `entityManager.persist(entity)`, `repository.save(entity)`| JPA/Hibernate identifiers mapping domain objects to relational DB.|
| Build Tools | `pom.xml`, `<dependency>`, `mvn clean package`, `mvn test`, `build.gradle`, `./gradlew build`| Maven/Gradle artifacts and commands.                                                        |
| Data Structures & Algorithms | `new ArrayList<>()`, `HashMap<K,V> map = new HashMap<>()`, `TreeMap<K,V>`, `PriorityQueue<E> pq = new PriorityQueue<>()`, `Collections.sort(list)`, `Arrays.sort(arr)`, `implements Comparable<T>`, `Comparator.comparing(...)`| Standard collections and sort/comparator interfaces.|
| File I/O & Serialization| `new File("path")`, `FileInputStream fis = new FileInputStream(file)`, `BufferedReader br = new BufferedReader(new FileReader("file"))`, `Files.readAllLines(Paths.get("file"))`, `ObjectOutputStream oos = new ObjectOutputStream(os)`, `implements Serializable`| Java IO primitives and serialization classes.|
| Networking (Sockets)| `Socket socket = new Socket(host, port)`, `ServerSocket server = new ServerSocket(port)`, `DatagramSocket ds = new DatagramSocket()`, `DatagramPacket packet = new DatagramPacket(buf, len)`, `InetAddress.getByName(host)`| Low-level socket APIs for TCP/UDP networking.|
| GUI Development| `new JFrame("title")`, `JPanel panel = new JPanel()`, `JButton btn = new JButton("OK")`, `addActionListener(...)`, `extends Application` (JavaFX), `@FXML`, `start(Stage stage)`| Swing/JavaFX GUI identifiers.|
| Design Patterns| Singleton: `private static Instance inst; private MyClass() {}`, Builder: `new Builder().setX().build()`, Factory: `Factory.create(type)`, Observer: `addListener(listener)`, Strategy: `context.setStrategy(new Impl())`| Typical pattern idioms visible in code.|
| Logging & Monitoring| `import org.slf4j.Logger`, `Logger logger = LoggerFactory.getLogger(MyClass.class)`, `logger.info("...")`, `logger.debug(...)`, `logger.error("...")`| Logging instrumentation usage.|
| Security & Crypto| `@PreAuthorize("hasRole('ADMIN')")`, `BCryptPasswordEncoder encoder = new BCryptPasswordEncoder()`, `Cipher.getInstance("AES")`, `MessageDigest.getInstance("SHA-256")`| Spring Security annotations and crypto APIs.|
| CI/CD & Deployment Automation| `.github/workflows/*.yml` references, `mvn -DskipTests package`, `Dockerfile` with `FROM openjdk:17-jdk`, `Jenkinsfile`| Build and pipeline artifacts common in Java projects.|
| CLI / Utility| `public static void main(String[] args)`, `System.out.println("...")`, `Scanner sc = new Scanner(System.in)`| Standard Java CLI entrypoints and IO.|
| Memory & Runtime Awareness| `System.gc()`, `ThreadLocal<T> local = new ThreadLocal<>()`, `WeakReference<T> wr = new WeakReference<>(obj)`, overriding `protected void finalize()`| JVM/garbage-collection and reference types usage.|
| Android (mobile)| `extends Activity`, `extends Fragment`, `Intent intent = new Intent(this, Other.class)`, `Bundle bundle = new Bundle()`, `RecyclerView`, `ViewModel`, `LiveData`, `implements Parcelable`| Android-specific APIs in Java.|


## Python
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Object-Oriented Programming (OOP) | `class MyClass:`, `def __init__(self):`, `self.attr`, `super().__init__()`, `@staticmethod`, `@classmethod`, `class SubClass(BaseClass):`, `import abc`, `from abc import ABC, abstractmethod`, `def __str__(self):`, `def __repr__(self):` | Python class and inheritance syntax, abstract base classes.                                         |
| Concurrency & Multithreading      | `import threading`, `threading.Thread(target=func).start()`, `thread.join()`, `import multiprocessing`, `multiprocessing.Process(target=...)`, `from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor`, `async def func():`, `await coro`, `import asyncio`, `asyncio.run(main())` | Threading, multiprocessing, asyncio, and futures primitives.                                        |
| Exception Handling & Robustness   | `try: ... except Exception as e: ... finally:`, `raise ValueError("msg")`, `with open('f') as f:`, `import logging`, `logging.exception(...)`, `assert condition` | Pythonic error handling and logging usage.                                                          |
| Unit Testing & TDD                | `import unittest`, `class TestX(unittest.TestCase):`, `def setUp(self):`, `self.assertEqual(a, b)`, `import pytest`, `def test_func():`, `with pytest.raises(ValueError):`, `unittest.mock.patch`, `MagicMock()` | unittest/pytest & mocking patterns.                                                                 |
| RESTful API Development           | `from flask import Flask, request, jsonify`, `@app.route('/path', methods=['GET'])`, `from fastapi import FastAPI`, `app = FastAPI()`, `@app.get("/items/{id}")`, `from django.urls import path`, `JsonResponse()` | Flask/FastAPI/Django routing & request/response constructs.                                         |
| Dependency Injection & IoC        | `-` (core language lacks native DI), `from dependency_injector import containers, providers`, `injector = Injector()` | Python usually uses factories and DI libraries; explicit DI libs show IoC use.                      |
| Functional Programming (FP)       | `map(func, iterable)`, `filter(func, iterable)`, `from functools import reduce`, `lambda x: x+1`, `[x for x in seq if x>0]`, `itertools.chain()`, `operator.itemgetter` | FP idioms and higher-order functions.                                                               |
| Data Persistence & ORM            | `import sqlite3`, `conn = sqlite3.connect('db')`, `cursor.execute(sql)`, `from sqlalchemy import Column, Integer, String`, `class User(Base): __tablename__='users'`, `session.query(User)`, `django.db.models.Model`, `User.objects.create()` | DB connectivity and ORMs (SQLAlchemy/Django ORM).                                                   |
| Build Tools                       | `requirements.txt`, `pip install -r requirements.txt`, `pyproject.toml`, `poetry add package`, `setup.py`, `python -m pip` | Python dependency management artifacts.                                                             |
| Data Structures & Algorithms      | `list`, `dict`, `set`, `tuple`, `heapq.heappush`, `bisect.insort`, `from collections import deque, Counter, defaultdict` | Core collections and algorithmic helpers.                                                           |
| File I/O & Serialization          | `open('file', 'r')`, `f.read()`, `json.load(f)`, `json.dump(obj, f)`, `pickle.dump(obj, f)`, `pickle.load(f)`, `with open(...) as f:` | File and serialization primitives.                                                                  |
| Networking (Sockets)              | `import socket`, `s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)`, `s.connect((host,port))`, `s.sendall(data)`, `s.recv(1024)`, `import asyncio`, `asyncio.start_server()` | Socket and async server APIs.                                                                       |
| GUI Development                   | `import tkinter as tk`, `root = tk.Tk()`, `Button(root, text='OK')`, `from PyQt5 import QtWidgets`, `class MyApp(QtWidgets.QMainWindow):` | GUI libraries and widgets.                                                                          |
| Design Patterns                   | Singleton: `class Singleton: _inst=None; def __new__(cls): ...`, Builder via fluent API, Factory functions, Strategy via passing callable | Python idioms for common patterns.                                                                  |
| Logging & Monitoring              | `import logging`, `logging.basicConfig(level=logging.INFO)`, `logger = logging.getLogger(__name__)`, `logger.info('msg')` | Standard logging framework usage.                                                                   |
| Security & Crypto                 | `import hashlib`, `hashlib.sha256(b'text')`, `import bcrypt`, `bcrypt.hashpw(pw, bcrypt.gensalt())`, `from cryptography.fernet import Fernet`, `jwt.encode(payload, key)` | Crypto and auth-related library calls.                                                              |
| CI/CD & Deployment Automation     | `.github/workflows/*.yml`, `pip wheel`, `pip install -r requirements.txt`, `Dockerfile FROM python:3.10` | Pipeline & container artifacts.                                                                     |
| CLI / Utility                     | `if __name__ == "__main__":`, `import argparse`, `parser = argparse.ArgumentParser()`, `args = parser.parse_args()`, `print()`, `input()` | Typical CLI entrypoint and argument parsing usage.                                                  |
| Memory & Runtime Awareness        | `import gc`, `gc.collect()`, `import sys`, `sys.getsizeof(obj)`, `import weakref`, `weakref.ref(obj)` | Tools to inspect/handle memory in Python.                                                           |
| Android (mobile)                  | `-` | Python is not typically used for native Android development (unless Kivy, BeeWare—those are niche). |


## JavaScript / Node.js
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language Core & OOP | `class MyClass { constructor() {} }`, `new MyClass()`, `this.prop`, `prototype.method = function() {}`, `function f() {}` | JS class syntax and prototypal inheritance patterns. |
| Asynchronous Programming | `Promise.resolve()`, `new Promise((res,rej) => {})`, `async function() {}`, `await promise`, `setTimeout(...)`, `setInterval(...)`, `process.nextTick()` | Core async primitives: promises and async/await. |
| Node.js / Server | `const http = require('http')`, `const express = require('express')`, `require('fs')`, `process.env`, `module.exports = ...`, `require('./file')` | Common Node server-side modules and module system. |
| Package & Build | `package.json`, `npm install`, `npx`, `yarn add`, `webpack.config.js` | Package manifest and build tool artifacts. |
| Testing | `jest`, `mocha`, `describe()`, `it()`, `expect()`, `sinon.stub()` | JS testing frameworks. |
| Functional Programming | `arr.map(x => x*2)`, `arr.filter(x => x>0)`, `arr.reduce((a,b)=>a+b,0)` | FP-style array methods. |


## TypeScript
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Typing & Interfaces | `interface IUser { id: number; name: string }`, `type ID = number | string`, `function foo(x: number): string {}`, `class MyClass implements IMy` | Static typing constructs that enhance code correctness. |
| Generics & Advanced Types | `function identity<T>(arg: T): T`, `Array<T>`, `Promise<T>` | Generic programming patterns in TS. |
| Compilation & Tooling | `tsconfig.json`, `tsc`, `npm run build` | TypeScript compilation artifacts. |


## C
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Low-level Systems & Memory | `#include <stdio.h>`, `int main(int argc, char **argv)`, `malloc(size)`, `free(ptr)`, `sizeof(type)`, pointer syntax `int *p`, `&var`, `*p = value` | C-level memory management and pointer usage. |
| Concurrency | `pthread_create(&tid, NULL, func, arg)`, `pthread_join(tid, NULL)`, `#include <pthread.h>` | POSIX thread APIs. |
| File I/O | `fopen("file","r")`, `fread(buf, 1, n, f)`, `fwrite(...)`, `fclose(f)` | Standard IO functions. |
| Compilation & Build | `gcc -o prog file.c`, `Makefile` | Build tool commands and artifacts. |
| Network Sockets | `#include <sys/socket.h>`, `socket(AF_INET, SOCK_STREAM, 0)`, `bind()`, `listen()`, `accept()`, `connect()` | Low-level socket system calls. |


## C++
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| OOP & Templates | `class MyClass { public: MyClass(); }`, `template<typename T> class Vector {}`, `std::unique_ptr<T>`, `std::shared_ptr<T>` | C++ classes, templates, and smart pointers. |
| STL & Algorithms | `std::vector<int> v;`, `std::map<K,V>`, `std::sort(v.begin(), v.end())`, `std::algorithm` | STL containers and algorithms. |
| Concurrency | `#include <thread>`, `std::thread t(func)`, `t.join()`, `std::mutex`, `std::lock_guard<std::mutex>` | C++11+ concurrency primitives. |
| File I/O | `#include <fstream>`, `std::ifstream ifs("file")`, `std::ofstream ofs("file")` | C++ stream-based IO. |


## C# / .NET
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| OOP & .NET Core | `public class MyClass { }`, `using System;`, `namespace MyApp { }`, `new MyClass()` | Core C# constructs and namespaces. |
| Async / Await | `async Task MyMethod() { await SomeAsync(); }` | Asynchronous programming model in .NET. |
| ASP.NET Core | `public class Startup`, `app.UseRouting()`, `app.UseEndpoints(endpoints => { endpoints.MapControllers(); })`, `[ApiController]`, `[HttpGet("{id}")]` | ASP.NET Core web framework idioms. |
| Dependency Injection | `public void ConfigureServices(IServiceCollection services) { services.AddScoped<IMy, MyImpl>(); }` | Built-in DI container usage. |
| Entity Framework | `DbContext`, `DbSet<T>`, `modelBuilder.Entity<T>()`, `AddAsync()` | EF Core ORM identifiers. |
| Build & Tooling | `.csproj`, `dotnet build`, `dotnet run`, `nuget` | .NET project and build artifacts. |


## Go
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language & Concurrency | `package main`, `func main() {}`, `go func() { }()`, `chan int`, `var wg sync.WaitGroup`, `select {}` | Go concurrency primitives (goroutines & channels). |
| Web / REST | `import "net/http"`, `http.HandleFunc("/path", handler)`, `http.ListenAndServe(":8080", nil)` | Standard library server patterns. |
| Modules & Build | `go.mod`, `go build`, `go test`, `go get` | Go modules and build commands. |
| Data Structures | `map[string]int`, `slice := []int{}`, `make(map[string]int)` | Native collection types. |


## Rust
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Ownership & Safety | `let x = String::from("x"); let y = x; // move`, `&x`, `&mut x`, `impl Trait for Struct {}`, `struct MyStruct {}` | Rust ownership/borrowing model visible via exact tokens. |
| Concurrency | `use std::thread; thread::spawn({ ... })`, `Arc<Mutex<T>>`, `async fn`, `tokio::spawn()` | Rust concurrency primitives and async runtimes. |
| Cargo & Build | `Cargo.toml`, `cargo build`, `cargo test` | Rust package manifest and build commands. |
| Error Handling | `Result<T, E>`, `?` operator, `panic!()` | Rust error patterns and propagation tokens. |


## PHP
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language Core | `<?php`, `echo "hello";`, `function foo($arg) {}`, `$var = 1;` | Standard PHP syntax tokens. |
| Web / Frameworks | `$_POST`, `$_GET`, `header("Location: /")`, `session_start()` | Common PHP web request handling primitives. |
| Composer & Build | `composer.json`, `composer install` | Package manager artifacts. |


## Ruby
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language Core | `class MyClass; def initialize; end; end`, `@instance_var`, `module MyModule; end`, `def method_name(arg)` | Ruby class and module syntax. |
| Gems & Build | `Gemfile`, `bundle install` | Package management artifacts. |


## R
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|


## MATLAB
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|


## SQL (MySQL / PostgreSQL / SQLite)
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| SQL DDL/DML | `SELECT * FROM table WHERE id = ?`, `INSERT INTO table (col) VALUES (...)`, `UPDATE table SET col = ? WHERE id = ?`, `DELETE FROM table WHERE id = ?`, `CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255))` | Core SQL statements across vendors. |
| Indexes & Transactions | `CREATE INDEX idx_name ON table(col)`, `BEGIN TRANSACTION`, `COMMIT`, `ROLLBACK` | Transactional and indexing primitives. |
| Joins & Aggregation | `INNER JOIN`, `LEFT JOIN`, `GROUP BY`, `ORDER BY`, `HAVING`, `COUNT(*)`, `SUM(col)` | Data joining and aggregation patterns. |


## Shell Scripting (Bash / zsh)
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Scripting & CLI | `#!/bin/bash`, `echo "hello"`, `read var`, `if [ -f file ]; then ... fi`, `for i in $(ls); do ... done` | Shell interpreter shebang and common control flow tokens. |
| Process & IO | `ps aux`, `grep`, `awk '{print $1}'`, `sed 's/a/b/g'`, `>&2` | Command-line utilities and stream editing. |
| Automation | `cron`, `crontab -e`, `chmod +x script.sh` | Scheduling and executable scripting patterns. |


## Swift
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language & iOS | `import UIKit`, `class ViewController: UIViewController { override func viewDidLoad() { } }`, `@IBOutlet weak var label: UILabel!`, `@IBAction func tapped(_ sender: Any) { }` | iOS app and Swift language constructs. |
| Networking | `URLSession.shared.dataTask(with: url) { data, resp, err in ... }` | URLSession async networking calls. |
| Build & Tooling | `Podfile`, `CocoaPods`, `Swift Package Manager`, `xcodeproj` | iOS build system artifacts. |


## Kotlin
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Language & Android | `class MyActivity : AppCompatActivity() { override fun onCreate(savedInstanceState: Bundle?) { } }`, `val x: Int = 1`, `var y = 2`, `fun foo(): String {}` | Kotlin language constructs and Android interoperability. |
| Coroutines & Concurrency | `import kotlinx.coroutines.*`, `GlobalScope.launch { ... }`, `suspend fun fetch() { }`, `withContext(Dispatchers.IO) { }` | Kotlin coroutines and structured concurrency. |
| DSL & Extension | `fun String.foo() = ...`, `build.gradle.kts` | Kotlin-specific language features. |


---

# Frameworks

## Spring Boot
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| RESTful API Development | `@SpringBootApplication`, `@RestController`, `@RequestMapping("/api")`, `@GetMapping("/items")`, `@PostMapping`, `@PathVariable`, `@RequestBody`, `ResponseEntity.ok()` | Spring Boot REST annotations and idioms.|
| Dependency Injection | `@Autowired`, `@Service`, `@Repository`, `@Component`, `@Configuration`, `@Bean` | Spring DI container usage.|
| Data Persistence / JPA   | `spring-boot-starter-data-jpa`, `@Entity`, `CrudRepository`, `JpaRepository`, `@Transactional` | Spring Data JPA integrations.|
| Security| `spring-boot-starter-security`, `@EnableWebSecurity`, `WebSecurityConfigurerAdapter`, `@PreAuthorize` | Spring Security configuration artifacts.  |
| Build & Deployment| `application.properties`, `application.yml`, `spring.profiles.active`, `mvn spring-boot:run`, `java -jar app.jar` | Configuration and Boot run commands.|
| Actuator & Monitoring| `spring-boot-starter-actuator`, `/actuator/health`, `management.endpoints.web.exposure.include=*` | Spring Actuator endpoints for monitoring. |
| Testing| `@SpringBootTest`, `@WebMvcTest`, `MockMvc mockMvc`, `@DataJpaTest` | Spring testing annotations and helpers.   |
| Configuration Properties | `@ConfigurationProperties(prefix="app")`, `@Value("${app.name}")` | Externalized configuration binding.|


## Django
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| RESTful API Development| `from django.urls import path`, `path('api/items/', views.items)`, `from rest_framework import viewsets`, `class ItemViewSet(viewsets.ModelViewSet):`, `@api_view(['GET'])`, `Response(data)` | Django and Django REST Framework routing and viewset idioms. |
| ORM & Persistence| `class Author(models.Model):`, `models.CharField(max_length=100)`, `ForeignKey(Author, on_delete=models.CASCADE)`, `Author.objects.filter(...)` | Django model declarations and ORM querysets.|
| Authentication & Security | `from django.contrib.auth.models import User`, `@login_required`, `permissions.IsAuthenticated`, `django.contrib.auth` | Built-in auth and permission system usage.|
| Configuration & Settings  | `settings.py`, `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES = { ... }` | Django config artifacts.|
| Templating & Views| `render(request, 'template.html', context)`, `{{ variable }}`, `class-based views: TemplateView` | Template and view constructs.|
| Testing| `from django.test import TestCase`, `client = Client()`, `self.client.get('/path/')` | Django testing utilities.|
| Migrations| `makemigrations`, `migrate`, `class Migration(migrations.Migration):` | DB migration commands and files.|


## Flask
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| RESTful API Development | `from flask import Flask, request, jsonify`, `app = Flask(__name__)`, `@app.route('/items', methods=['GET'])`, `return jsonify({'k':'v'})` | Flask core app and route decorators.|
| Dependency Injection| `-` (no native DI; use Flask extensions or patterns) | Flask is minimal; DI achieved by extension patterns rather than language constructs. |
| Templates & Views| `from flask import render_template`, `templates/index.html`, `{{ var }}` | Jinja2 templating usage.|
| Extensions & Blueprints | `from flask import Blueprint`, `bp = Blueprint('bp', __name__)`, `app.register_blueprint(bp)` | App structuring patterns.|
| Testing| `app.test_client()`, `pytest`, `with app.test_client() as c:` | Flask testing client usage.|


## FastAPI
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| RESTful API Development | `from fastapi import FastAPI`, `app = FastAPI()`, `@app.get("/items/{id}")`, `from pydantic import BaseModel`, `def read_item(item_id: int):` | FastAPI route decorators and pydantic models. |
| Data Validation | `class Item(BaseModel): name: str; price: float` | Pydantic model usage for validation and serialization. |
| Async Support | `async def get_item():`, `await some_call()` | Native async route support in FastAPI. |
| Dependency Injection | `from fastapi import Depends`, `def get_db(): ...`, `db = Depends(get_db)` | FastAPI's built-in dependency injection primitives. |


## React
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| UI Components | `function MyComp(props) { return (<div/>); }`, `class MyComp extends React.Component { render() { } }`, `return (<JSX />)` | Component definitions in functional and class forms. |
| Hooks & State | `const [state, setState] = useState(initial)`, `useEffect(() => {}, [])`, `useContext(MyContext)` | React hooks and lifecycle management in function components. |
| Props & Context | `<MyComp prop={value} />`, `React.createContext(default)`, `<MyContext.Provider value={...}>` | Component communication and context APIs. |
| Routing | `import { BrowserRouter, Route } from 'react-router-dom'`, `<Route path="/home" component={Home} />` | Client-side routing patterns. |
| State Management | `import { createStore } from 'redux'`, `useReducer()`, `dispatch({ type: 'X' })` | Redux / context / reducer patterns for app state. |


## Angular
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Components & Templates | `@Component({ selector: 'app-root', templateUrl: './app.component.html' })`, `export class AppComponent { }`, `<app-root></app-root>` | Angular component decorator & template usage. |
| Dependency Injection | `constructor(private service: MyService) {}`, `@Injectable({ providedIn: 'root' })` | Built-in DI via constructor injection and providers. |
| Routing | `RouterModule.forRoot(routes)`, `<router-outlet></router-outlet>`, `{ path: 'home', component: HomeComponent }` | Angular routing module patterns. |
| Forms & RxJS | `import { FormGroup, FormControl } from '@angular/forms'`, `import { Observable } from 'rxjs'`, `observable.pipe(map(...))` | Reactive forms and RxJS observables. |


## Vue
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Components & Templates | `Vue.component('my-comp', { template: '<div></div>' })`, `export default { name: 'MyComp', data() { return {} } }`, `<template>...</template>` | Vue single-file component and options API. |
| Reactive Data | `data() { return { count: 0 } }`, `computed: { ... }`, `watch: { ... }` | Vue reactivity through data/computed/watchers. |
| Vue Router & Vuex | `import VueRouter from 'vue-router'`, `new VueRouter({ routes })`, `import Vuex from 'vuex'`, `new Vuex.Store({...})` | Routing and state management patterns. |


## Svelte
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|


## Express.js
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| RESTful API Development | `const express = require('express')`, `const app = express()`, `app.get('/path', (req, res) => {})`, `app.post('/path', (req, res) => {})`, `app.use(express.json())` | Express route and middleware patterns. |
| Middleware & Error Handling | `app.use((err, req, res, next) => {})`, `next(err)` | Express error middleware patterns. |
| Routing & Modularity | `const router = express.Router()`, `router.get('/', handler)`, `app.use('/api', router)` | Router and modularization idioms. |


## Laravel
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| MVC & Routing | `Route::get('/users', 'UserController@index')`, `php artisan make:controller`, `return view('users.index')` | Laravel routing and controller/view idioms. |
| Eloquent ORM | `class User extends Model`, `User::where('id', $id)->first()`, `$user->save()` | ORM model declarations and queries. |
| Middleware & Auth | `php artisan make:middleware`, `Auth::user()`, `auth()->user()` | Auth and middleware helpers. |


## Ruby on Rails
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| MVC & Routing | `Rails.application.routes.draw do`, `resources :users`, `class UsersController < ApplicationController` | Rails routing and controller conventions. |
| ActiveRecord | `class User < ApplicationRecord`, `has_many :posts`, `User.find_by(email: email)` | ORM model and relationship identifiers. |
| Migrations & Rake | `rails db:migrate`, `class CreateUsers < ActiveRecord::Migration[6.0]` | Database migration artifacts. |


## Android (Java/Kotlin)
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Android App Components | `extends Activity`, `extends AppCompatActivity`, `extends Fragment`, `onCreate(Bundle savedInstanceState)`, `setContentView(R.layout.activity_main)` | Core Android lifecycle and components in Java/Kotlin. |
| Intents & Navigation   | `new Intent(this, Target.class)`, `intent.putExtra("key", value)`, `startActivity(intent)`, `NavController.navigate(R.id.action)` | Navigation & inter-component messaging.               |
| UI Components          | `RecyclerView`, `Adapter`, `ViewHolder`, `findViewById(R.id.x)`, `DataBindingUtil.setContentView(...)`, `ViewModelProviders.of(this).get(MyViewModel.class)` | UI building blocks & patterns.                        |
| Persistence            | `Room.databaseBuilder(context, AppDatabase.class, "db")`, `@Entity`, `@Dao`, `preferences.getSharedPreferences(...)` | Mobile persistence APIs.                              |
| Background work        | `WorkManager`, `AsyncTask` (deprecated), `HandlerThread`, `JobScheduler`, `AlarmManager` | Scheduling and background tasks.                      |
| Permissions & Security | `Manifest.permission.ACCESS_FINE_LOCATION`, `requestPermissions(new String[]{...}, CODE)` | Runtime permission handling.                          |
| Gradle & Build         | `build.gradle`, `apply plugin: 'com.android.application'`, `minSdkVersion`, `targetSdkVersion` | Android Gradle identifiers.                           |


## iOS (Swift)
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|


## TensorFlow
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Neural networks & TF API | `import tensorflow as tf`, `tf.keras.Model`, `tf.keras.layers.Dense(64, activation='relu')`, `model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')`, `model.fit(x, y, epochs=10)` | TF Keras & graph/estimator APIs. |


## PyTorch
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Dynamic graphs & torch API | `import torch`, `class Net(nn.Module): def forward(self, x): ...`, `torch.tensor([1,2])`, `optimizer = torch.optim.Adam(model.parameters())`, `loss.backward()` | PyTorch module and training loop tokens. |


## NumPy
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Numerical Arrays & Ops | `import numpy as np`, `np.array([1,2,3])`, `np.dot(a, b)`, `np.reshape(arr, (n,m))`, `np.mean(arr)` | Core NumPy API used for numerical computation. |


## Pandas
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| DataFrame & IO | `import pandas as pd`, `pd.DataFrame(data)`, `df.head()`, `df.groupby('col').agg(...)`, `pd.read_csv('file.csv')`, `df.to_csv('out.csv')` | DataFrame operations & IO indicate tabular data skills. |


## Hadoop
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| HDFS & MapReduce | `hdfs dfs -ls /`, `hadoop jar`, `map(...) reduce(...)`, `YARN`, `core-site.xml`, `hdfs-site.xml` | HDFS commands and MapReduce/YARN config tokens. |


## Spark
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Spark Core & DataFrame | `spark-submit --class`, `SparkSession.builder.appName("...").getOrCreate()`, `df = spark.read.csv("...")`, `df.groupBy('col').agg({'col':'sum'})`, `rdd.map(lambda x: ...)` | SparkSession, DataFrame and RDD APIs. |


---

# DevOps / Cloud

## Docker
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Container Definitions & Commands | `Dockerfile`, `FROM openjdk:17-jdk`, `COPY . /app`, `RUN mvn package`, `EXPOSE 8080`, `docker build -t myapp .`, `docker run -p 8080:8080 myapp` | Dockerfile syntax and CLI commands used in containerized deployments. |


## Kubernetes
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| K8s Manifests & Commands | `apiVersion: apps/v1`, `kind: Deployment`, `kubectl apply -f deployment.yaml`, `kubectl get pods`, `service.yaml`, `ingress.yaml` | Kubernetes manifest fields and CLI commands. |


## Terraform
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| IaC & Resources | `provider "aws" {}`, `resource "aws_instance" "web" {}`, `terraform init`, `terraform apply`, `.tf` files` | Terraform HCL resource declarations and lifecycle commands. |


## AWS
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| AWS CLI & Services | `aws s3 cp file s3://bucket/`, `AWS_ACCESS_KEY_ID`, `aws lambda create-function`, `CloudFormation: AWSTemplateFormatVersion`, `IAM role`, `arn:aws:s3:::bucket` | CLI and resource naming conventions specific to AWS. |


## Azure
|**Skill**|**Identifier**|**Justification**|
|--------|--------|--------|
| Azure CLI & ARM | `az group create`, `az vm create`, `az storage blob upload`, `ARM templates`, `Resource Group` | Azure CLI commands and ARM template constructs. |

---