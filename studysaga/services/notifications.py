def notify_info(title, message):
  try:
    from plyer import notification
    notification.notify(title=title, message=message, timeout=2)
  except Exception:
    print(f"[NOTIFY] {title}: {message}")
