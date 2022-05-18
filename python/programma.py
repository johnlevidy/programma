from ortools.sat.python import cp_model
from input_types import Task, Milestone

people = ['ThingOne', 'ThingTwo']
taskB = Task('B', 3, None)
taskD = Task('D', 1, None)
taskC = Task('C', 2, taskD)
taskA = Task('A', 1, [taskB, taskC])
tasks = [taskA, taskB, taskC, taskD]
milestones = [Milestone("Project complete!", 5, [taskA])]

def max_day():
    return max(map(lambda x: x.due, milestones))

def model_builder():
    model = cp_model.CPModel()
    # do stuff
    print("Building model")

def main():
    # For now we assume everything can at least get done
    # in double the max due date
    boundary_day = max_day() * 2

    # number things, maybe more performant
    people_num = range(0, len(people))
    task_num = range(0, len(tasks))
    day_num = range(0, boundary_day)

    # Flexible job shop problem where you have
    # task ordering
    # people = machines
    # duration = processing_time
    # somehow have to model EndBeforeStart(j, i) http://www.optimization-online.org/DB_FILE/2019/10/7452.pdf
if __name__ == '__main__':
    main()
