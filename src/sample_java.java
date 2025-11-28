// SampleTest.java
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.regex.Pattern;

public class sample_java {

    public static void main(String[] args) {
        // Object-Oriented Programming: class + method usage
        sample_java obj = new sample_java();
        obj.printMessage("Hello, world!");

        // Data Structures: ArrayList
        List<String> list = new ArrayList<>();
        list.add("Java");
        list.add("Python");

        List<String> list2 = new ArrayList<>();

        // Concurrency & Multithreading
        ExecutorService executor = Executors.newFixedThreadPool(2);
        executor.submit(() -> System.out.println("Task 1"));
        executor.submit(() -> System.out.println("Task 2"));
        executor.shutdown();

        // Exception Handling
        try {
            int result = divide(10, 0);
        } catch (ArithmeticException e) {
            System.out.println("Cannot divide by zero!");
        }

        // Functional Programming: streams
        list.stream().forEach(System.out::println);

        // Regex example
        String input = "abc123";
        if (Pattern.matches("\\w+\\d+", input)) {
            System.out.println("Regex matched!");
        }
    }

    public void printMessage(String message) {
        System.out.println(message);
    }

    public static int divide(int a, int b) {
        return a / b;
    }
}