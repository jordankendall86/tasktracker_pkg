from tasktracker import TaskManager, JsonStorage

#Create a TaskManager:
manager = TaskManager()
#Add Tasks:
manager.add_task("Write report", "Finish the quarterly report")
manager.add_task("Review PR", "Check the new feature pull request")
#Complete a Task:
manager.complete_task(0)

#Create a JsonStorage:
storage = JsonStorage("tasks.json")
#Save Tasks:
storage.save(manager.list_tasks())
#Load Tasks:
loaded_tasks = storage.load()
#List Tasks:
for i, task in enumerate(loaded_tasks, start=1):
    status = "Done" if task.completed else "Pending"
    print(f"{i}. {task.title} - {status}")
