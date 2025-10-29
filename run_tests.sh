#!/bin/bash

echo "🧪 SMARTSCHOOL MONITOR - TEST SUITE"
echo "====================================="
echo ""

echo "📊 TEST 1: View Current Status"
echo "-------------------------------"
python view_homework.py 2>/dev/null | grep -E "Student|homework items|Token valid"
echo ""

echo "🔄 TEST 2: Quick Check (No New Homework)"
echo "-----------------------------------------"
python test_monitor.py 2>&1 | grep -E "Found.*homework items"
echo ""

echo "✨ TEST 3: Simulate New Homework Detection"
echo "-------------------------------------------"
python test_new_homework.py 2>&1 | grep "New homework detected"
echo ""

echo "✅ ALL TESTS COMPLETE!"
echo ""
echo "📖 For detailed testing guide: cat TESTING_GUIDE.md"
echo "📋 To view homework anytime: python view_homework.py"
