package com.stockmaster.inventory.controller;

import com.stockmaster.inventory.entity.Product;
import com.stockmaster.inventory.repository.ProductRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/inventory")
@CrossOrigin(origins = "*")
public class InventoryController {
    
    @Autowired
    private ProductRepository productRepository;
    
    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final DateTimeFormatter TIMESTAMP_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private final List<String> recentAuditLogs = Collections.synchronizedList(new ArrayList<>());

    @GetMapping("/low-stock")
    public ResponseEntity<List<Product>> getLowStockProducts() {
        List<Product> lowStock = productRepository.findLowStockProducts();
        return ResponseEntity.ok(lowStock);
    }
    
    @GetMapping("/products")
    public ResponseEntity<List<Product>> getAllProducts() {
        return ResponseEntity.ok(productRepository.findAll());
    }
    
    @GetMapping("/products/{id}")
    public ResponseEntity<Product> getProductById(@PathVariable Integer id) {
        return productRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
    
    @PostMapping("/products")
    public ResponseEntity<Product> createProduct(@RequestBody Product product) {
        return ResponseEntity.ok(productRepository.save(product));
    }
    
    @PutMapping("/products/{id}")
    public ResponseEntity<Product> updateProduct(@PathVariable Integer id, @RequestBody Product product) {
        return productRepository.findById(id)
                .map(existing -> {
                    product.setId(id);
                    return ResponseEntity.ok(productRepository.save(product));
                })
                .orElse(ResponseEntity.notFound().build());
    }
    
    @DeleteMapping("/products/{id}")
    public ResponseEntity<Void> deleteProduct(@PathVariable Integer id) {
        if (productRepository.existsById(id)) {
            productRepository.deleteById(id);
            return ResponseEntity.ok().build();
        }
        return ResponseEntity.notFound().build();
    }
    
    @PostMapping("/restock")
    public ResponseEntity<Product> restockProduct(@RequestBody Map<String, Object> request) {
        Integer productId = (Integer) request.get("productId");
        Integer quantity = (Integer) request.get("quantity");
        String commandText = Optional.ofNullable(request.get("commandText")).map(Object::toString).orElse("Restock command received");
        
        return productRepository.findById(productId)
                .map(product -> {
                    product.setQuantity(product.getQuantity() + quantity);
                    Product updated = productRepository.save(product);
                    
                    logAudit(productId, "Restock", quantity);
                    appendReasoningFeed("USER COMMAND: " + commandText);
                    
                    return ResponseEntity.ok(updated);
                })
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/add")
    public ResponseEntity<Product> addProduct(@RequestBody Product product) {
        Product saved = productRepository.save(product);
        appendReasoningFeed("USER COMMAND: Add new item " + product.getName());
        return ResponseEntity.ok(saved);
    }

    @PostMapping("/simulate-shortage")
    public ResponseEntity<Product> simulateShortage() {
        List<Product> products = productRepository.findAll();
        if (products.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        Random random = new Random();
        Product chosen = products.get(random.nextInt(products.size()));
        int newQuantity = Math.max(1, chosen.getThreshold() - 2);
        chosen.setQuantity(newQuantity);
        Product updated = productRepository.save(chosen);

        appendReasoningFeed("USER COMMAND: Simulate shortage for " + chosen.getName());
        appendReasoningFeed("SYSTEM: Forced shortage detected for " + chosen.getName() + " (qty=" + newQuantity + ")");
        logAudit(chosen.getId(), "Missing Shipment - System Simulation", chosen.getThreshold() - newQuantity);

        return ResponseEntity.ok(updated);
    }

    @PostMapping("/run-bi")
    public ResponseEntity<Map<String, Object>> runBusinessIntelligence() {
        try {
            Path scriptPath = Paths.get(System.getProperty("user.dir")).resolve("../openclaw-agent/skills/analyze_performance.py").normalize();
            ProcessBuilder builder = new ProcessBuilder("python", scriptPath.toString());
            builder.directory(Paths.get(System.getProperty("user.dir")).toFile());
            Process process = builder.start();

            String output;
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                output = reader.lines().collect(Collectors.joining("\n"));
            }
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                return ResponseEntity.status(500).body(Map.of("error", "BI analysis failed"));
            }

            Map<String, Object> result = objectMapper.readValue(output, new TypeReference<Map<String, Object>>() {});
            appendReasoningFeed("USER COMMAND: Run BI Analysis");
            appendReasoningFeed("SYSTEM: BI Analysis executed on demand");
            return ResponseEntity.ok(result);
        } catch (IOException | InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(500).body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        appendReasoningFeed("USER COMMAND: System Health Check");
        return ResponseEntity.ok(Map.of(
                "status", "ok",
                "timestamp", LocalDateTime.now().format(TIMESTAMP_FORMAT)
        ));
    }

    @GetMapping(value = "/reasoning", produces = MediaType.TEXT_PLAIN_VALUE)
    public ResponseEntity<String> getReasoningFeed() {
        try {
            Path feedFile = Paths.get(System.getProperty("user.dir")).resolve("../openclaw-agent/reasoning_feed.txt").normalize();
            if (!Files.exists(feedFile)) {
                return ResponseEntity.ok("");
            }
            String content = Files.readString(feedFile, StandardCharsets.UTF_8);
            return ResponseEntity.ok(content);
        } catch (IOException e) {
            return ResponseEntity.status(500).body("Unable to read reasoning feed");
        }
    }

    @GetMapping("/agent/context")
    public ResponseEntity<Map<String, Object>> getAgentContext() {
        List<Product> lowStock = productRepository.findLowStockProducts();
        return ResponseEntity.ok(Map.of(
                "lowStock", lowStock,
                "auditLogs", new ArrayList<>(recentAuditLogs)
        ));
    }
    
    private void logAudit(Integer productId, String action, Integer quantity) {
        String logEntry = "AUDIT: Product " + productId + " - " + action + " - Quantity/Diff: " + quantity + " @ " + LocalDateTime.now().format(TIMESTAMP_FORMAT);
        System.out.println(logEntry);
        recentAuditLogs.add(logEntry);
        if (recentAuditLogs.size() > 100) {
            recentAuditLogs.remove(0);
        }
    }
    
    private void appendReasoningFeed(String entry) {
        try {
            Path feedFile = Paths.get(System.getProperty("user.dir")).resolve("../openclaw-agent/reasoning_feed.txt").normalize();
            Files.createDirectories(feedFile.getParent());
            String timestamped = "[" + LocalDateTime.now().format(TIMESTAMP_FORMAT) + "] " + entry + System.lineSeparator();
            Files.writeString(feedFile, timestamped, StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            System.err.println("Unable to write reasoning feed: " + e.getMessage());
        }
    }
}
