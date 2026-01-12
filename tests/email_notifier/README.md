# Email Notifier Tests

Comprehensive unit tests for the email_notifier module.

## Test Coverage

### test_notifier.py (22 tests)
Tests for the `EmailNotifier` class:

#### Initialization Tests
- `test_init` - Basic initialization with valid config
- `test_init_default_port` - Default port assignment (587)
- `test_init_empty_recipients` - Handling empty recipient list

#### Configuration Validation Tests
- `test_validate_config_valid` - Valid configuration passes
- `test_validate_config_no_smtp_server` - Fails without SMTP server
- `test_validate_config_no_sender_email` - Fails without sender email
- `test_validate_config_no_password` - Fails without password
- `test_validate_config_no_recipients` - Fails without recipients

#### Recipient Management Tests
- `test_add_recipient` - Adding new recipient
- `test_add_duplicate_recipient` - Prevents duplicate recipients
- `test_remove_recipient` - Removing existing recipient
- `test_remove_nonexistent_recipient` - Handling removal of non-existent recipient

#### Email Sending Tests (with mocked SMTP)
- `test_send_test_email_success` - Successful test email
- `test_send_email_smtp_auth_error` - SMTP authentication failure handling
- `test_send_email_smtp_exception` - SMTP exception handling
- `test_send_email_general_exception` - General exception handling
- `test_send_milestone_alert_success` - Successful milestone alert
- `test_send_milestone_alert_empty_lists` - Alert with no milestones/games
- `test_send_milestone_alert_template_error` - Template generation error handling

#### Email Structure Tests
- `test_send_email_creates_correct_message_structure` - MIME message structure
- `test_send_email_uses_tls` - TLS encryption enabled
- `test_multiple_recipients` - Sending to multiple recipients

### test_templates.py (26 tests)
Tests for the `EmailTemplate` class:

#### Subject Generation Tests
- `test_generate_subject_with_games` - Subject with games
- `test_generate_subject_no_games` - Subject without games
- `test_generate_subject_one_game` - Subject with one game

#### HTML Generation Tests
- `test_generate_html_with_milestones_and_games` - Full HTML with both
- `test_generate_html_only_milestones` - HTML with only milestones
- `test_generate_html_only_games` - HTML with only games
- `test_generate_html_empty_lists` - HTML with empty data
- `test_generate_html_multiple_milestones` - Multiple milestones display
- `test_generate_html_progress_bar` - Progress bar rendering
- `test_generate_html_progress_bar_caps_at_100` - Progress bar caps at 100%
- `test_generate_html_estimated_games` - Estimated games display
- `test_generate_html_no_estimated_games` - Handling None estimates
- `test_generate_html_away_game` - Away game display
- `test_generate_html_game_no_time` - Game without time (TBD)
- `test_generate_html_styles_included` - CSS styles present

#### Text Version Tests
- `test_generate_text_version_with_milestones_and_games` - Full text version
- `test_generate_text_version_only_milestones` - Text with only milestones
- `test_generate_text_version_only_games` - Text with only games
- `test_generate_text_version_empty_lists` - Text with empty data
- `test_generate_text_version_formatting` - Text formatting (separators, indentation)
- `test_generate_text_version_percentage` - Percentage display
- `test_generate_text_version_multiple_games` - Multiple games display
- `test_generate_text_version_footer` - Footer content

#### Integration & Edge Case Tests
- `test_html_and_text_contain_same_info` - Parity between HTML and text
- `test_special_characters_in_player_name` - Special character handling
- `test_large_numbers_formatted_correctly` - Large number display

## Running Tests

Run all email_notifier tests:
```bash
python -m pytest tests/email_notifier/ -v
```

Run specific test file:
```bash
python -m pytest tests/email_notifier/test_notifier.py -v
python -m pytest tests/email_notifier/test_templates.py -v
```

Run specific test:
```bash
python -m pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init -v
```

## Test Results

**Total Tests: 48**
- EmailNotifier tests: 22
- EmailTemplate tests: 26

**Status: ✅ All tests passing**

## Test Dependencies

The tests use the following:
- `pytest` - Test framework
- `unittest.mock` - Mocking SMTP for isolated testing
- `datetime` - Date/time fixtures

## Mock Strategy

### SMTP Mocking
All tests that involve email sending use mocked SMTP connections:
- `@patch('src.email_notifier.notifier.smtplib.SMTP')` - Mocks SMTP server
- Tests verify correct methods are called without actually sending emails
- Different error scenarios are simulated (auth failure, connection errors)

### Template Mocking
Template generation tests in test_notifier.py mock EmailTemplate methods to isolate EmailNotifier logic.

## Test Fixtures

### Common Fixtures in test_notifier.py
- `valid_config` - Valid email configuration dictionary
- `notifier` - EmailNotifier instance with valid config
- `sample_milestone` - MilestoneProximity object for testing
- `sample_game` - Game object for testing

### Common Fixtures in test_templates.py
- `sample_milestone_close` - Milestone at 98.5% completion
- `sample_milestone_far` - Milestone at 80% completion
- `sample_milestone_at_100` - Milestone at exactly 100%
- `sample_home_game` - Home game fixture
- `sample_away_game` - Away game fixture
- `sample_game_no_time` - Game without specified time

## Coverage Areas

### EmailNotifier Class
- ✅ Initialization and configuration
- ✅ Configuration validation
- ✅ Recipient management (add/remove)
- ✅ Email sending (test and milestone alerts)
- ✅ SMTP connection and authentication
- ✅ Error handling (auth errors, SMTP exceptions, general exceptions)
- ✅ MIME message structure
- ✅ TLS encryption

### EmailTemplate Class
- ✅ Subject line generation
- ✅ HTML email generation
- ✅ Plain text email generation
- ✅ Progress bars and percentages
- ✅ Game information display (home/away, times)
- ✅ Milestone proximity display
- ✅ Estimated games to milestone
- ✅ Empty data handling
- ✅ Multiple items handling
- ✅ CSS styling
- ✅ Special characters
- ✅ Large numbers
- ✅ Edge cases (100% completion, missing data)

## Future Test Enhancements

Potential areas for additional testing:
- [ ] Integration tests with real (test) SMTP server
- [ ] Performance tests for large datasets
- [ ] HTML rendering tests (validate HTML structure)
- [ ] Email client compatibility tests
- [ ] Rate limiting tests (when implemented)
- [ ] Attachment tests (when implemented)
- [ ] Template customization tests (when implemented)
