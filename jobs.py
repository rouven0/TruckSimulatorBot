from dataclasses import dataclass

def list_from_tuples(tups):
    """
    Returns a list with all Jobs generated from a set of tuples from the database
    """
    jobs = []
    for tup in tups:
        jobs.append(from_tuple(tup))
    return jobs

def from_tuple(tup):
    """
    Returns a Job object from a received database tuple
    """
    return Job(tup[0], get_position(tup[1]), get_position(tup[2]), tup[3], tup[4])

def to_tuple(job):
    """
    Transforms the job object into a tuple that can be inserted in the db
    """
    return (job.job_id, format_pos_to_db(job.place_from), format_pos_to_db(job.place_to),
            job.state, job.reward)

def get_position(db_pos):
    """
    Parses the position from the database as list [x][y]
    """
    pos_x = db_pos[:db_pos.find("/")]
    pos_y = db_pos[db_pos.find("/")+1:]
    return [int(pos_x), int(pos_y)]

def format_pos_to_db(pos):
    """
    Returns a database-ready string that contains the position in the form x/y
    """
    return "{}/{}".format(pos[0], pos[1])

@dataclass
class Job():
    job_id: str
    place_from: list
    place_to: list
    state: int
    reward: int
