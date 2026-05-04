package com.stockmaster.inventory.controller;

import com.stockmaster.inventory.entity.Settings;
import com.stockmaster.inventory.repository.SettingsRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class SettingsController {

    @Autowired
    private SettingsRepository settingsRepository;

    @GetMapping("/settings")
    public ResponseEntity<Settings> getSettings() {
        Optional<Settings> settings = settingsRepository.findTopByOrderByIdAsc();
        return ResponseEntity.ok(settings.orElseGet(Settings::new));
    }

    @PostMapping("/settings")
    public ResponseEntity<Settings> saveSettings(@RequestBody Settings request) {
        Settings settings = settingsRepository.findTopByOrderByIdAsc().orElse(new Settings());
        settings.setStoreName(request.getStoreName());
        settings.setOwnerName(request.getOwnerName());
        settings.setChannel(request.getChannel());
        settings.setChannelId(request.getChannelId());
        settings.setCreatedAt(java.time.LocalDateTime.now());
        return ResponseEntity.ok(settingsRepository.save(settings));
    }
}