package com.stockmaster.inventory.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.context.request.WebRequest;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleAllExceptions(Exception ex, WebRequest request) {
        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now());
        errorDetails.put("message", "System Health Alert: Nervous System experiencing issues");
        errorDetails.put("error", ex.getMessage());
        errorDetails.put("path", request.getDescription(false).replace("uri=", ""));

        // Log the error for monitoring
        System.err.println("SYSTEM HEALTH ALERT: " + ex.getMessage());
        ex.printStackTrace();

        return new ResponseEntity<>(errorDetails, HttpStatus.INTERNAL_SERVER_ERROR);
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, Object>> handleRuntimeException(RuntimeException ex, WebRequest request) {
        Map<String, Object> errorDetails = new HashMap<>();
        errorDetails.put("timestamp", LocalDateTime.now());
        errorDetails.put("message", "System Health Alert: Runtime error detected");
        errorDetails.put("error", ex.getMessage());
        errorDetails.put("path", request.getDescription(false).replace("uri=", ""));

        System.err.println("SYSTEM HEALTH ALERT: " + ex.getMessage());

        return new ResponseEntity<>(errorDetails, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}