import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final String? imageContext; // Optional: what AI saw

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.imageContext,
  });

  Map<String, dynamic> toJson() => {
    'text': text,
    'isUser': isUser,
    'timestamp': timestamp.toIso8601String(),
    'imageContext': imageContext,
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
    text: json['text'],
    isUser: json['isUser'],
    timestamp: DateTime.parse(json['timestamp']),
    imageContext: json['imageContext'],
  );
}

class ChatHistoryService {
  static const String _key = 'wayfinder_chat_history';
  static const int _maxMessages = 100; // Keep last 100 messages

  Future<List<ChatMessage>> loadHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final String? jsonString = prefs.getString(_key);
      
      if (jsonString == null) return [];
      
      final List<dynamic> jsonList = json.decode(jsonString);
      return jsonList.map((json) => ChatMessage.fromJson(json)).toList();
    } catch (e) {
      print('Error loading chat history: $e');
      return [];
    }
  }

  Future<void> saveHistory(List<ChatMessage> messages) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // Keep only last N messages to avoid storage bloat
      final messagesToSave = messages.length > _maxMessages
          ? messages.sublist(messages.length - _maxMessages)
          : messages;
      
      final jsonList = messagesToSave.map((msg) => msg.toJson()).toList();
      final jsonString = json.encode(jsonList);
      
      await prefs.setString(_key, jsonString);
    } catch (e) {
      print('Error saving chat history: $e');
    }
  }

  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }

  Future<void> addMessage(ChatMessage message, List<ChatMessage> currentMessages) async {
    currentMessages.add(message);
    await saveHistory(currentMessages);
  }
}
