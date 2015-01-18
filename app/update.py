from app.coursepoll import UCMCoursePoll


def UpdateDB(poller_name, create_db=False):
    """ Takes a School name and updates its database or optionally creates all database entries. """
    poller = None
    if poller_name == 'UC Merced':
        poller = UCMCoursePoll(create_db)

    if poller is None:
        raise RuntimeError('Could not find the poller named %s' % (poller_name))

    return poller.GetCourseRequests()


if __name__ is '__main__':
    Update('UC Merced', true)
