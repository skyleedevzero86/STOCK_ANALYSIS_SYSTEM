-- 샘플 알림 설정 데이터
INSERT INTO notification_settings 
(user_email, symbol, notification_types, rsi_threshold, volume_spike_threshold, price_change_threshold, is_active) 
VALUES 
('analyst@company.com', NULL, '{"anomaly_alerts": true, "analysis_reports": true}', 70.0, 2.0, 5.0, TRUE),
('trader@company.com', 'AAPL', '{"anomaly_alerts": true, "analysis_reports": false}', 80.0, 3.0, 3.0, TRUE),
('manager@company.com', 'GOOGL', '{"anomaly_alerts": false, "analysis_reports": true}', 60.0, 1.5, 7.0, TRUE),
('investor@company.com', NULL, '{"anomaly_alerts": true, "analysis_reports": true}', 75.0, 2.5, 4.0, TRUE);

-- 알림 로그 조회 쿼리 예시
-- SELECT 
--     user_email,
--     symbol,
--     notification_type,
--     status,
--     sent_at,
--     SUBSTRING(message, 1, 100) as message_preview
-- FROM notification_logs 
-- WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
-- ORDER BY sent_at DESC;

-- 알림 통계 쿼리 예시
-- SELECT 
--     DATE(sent_at) as date,
--     notification_type,
--     status,
--     COUNT(*) as count
-- FROM notification_logs 
-- WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
-- GROUP BY DATE(sent_at), notification_type, status
-- ORDER BY date DESC;
