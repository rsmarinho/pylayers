"""

This module is based on Steering Behaviors for Autonomous Characters
created by Craig Reynolds and expanded upon by many.

    http://www.red3d.com/cwr/steer/
    http://www.red3d.com/cwr/papers/1999/gdc99steer.html
    http://opensteer.sourceforge.net/
    http://www.steeringbehaviors.de/


Seek Class
===========

.. autosummary::
    :toctree: generated

    Seek.calculate

Arrive Class
==============

.. autosummary::
    :toctree: generated

    Arrive.calculate

Wander Class
==============

.. autosummary::
    :toctree: generated

    Wander.calculate

Wander Class
==============

.. autosummary::
    :toctree: generated

    FollowWaypoints.calculate


Separation Class
=================

.. autosummary::
    :toctree: generated

    Separation.calculate


Queuing Class
=================

.. autosummary::
    :toctree: generated

    Separation.calculate


Containment Class
=================

.. autosummary::
    :toctree: generated

    Separation.calculate


"""

from math import *
from pylayers.mobility.transit.World import world
from pylayers.mobility.transit.vec3 import vec3
from random import uniform,gauss,randint
import pdb

# max front distance to consider 
FCHK = 2.0
# max side distance to consider 
SCHK = 2.

class Seek:
    """ class Seek

    Methods
    -------

    calculate

    """
    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Notes
        -----

        This behavior is the attraction by the destination POI
        The desired velocity is oriented toward the destination and scaled with
        the desired velocity.

        If the distance between current position and destination is less than
        25cm the boid has got its target point.


        """
        displacement = boid.destination - boid.position
        desired_velocity = displacement.normalize() * boid.desired_speed
        steering = desired_velocity - boid.velocity
        if (displacement.length() < 2*boid.radius):
            boid.arrived = True
        return steering

class Arrive:
    """ Class Arrive

    Methods
    -------

    calculate

    Notes
    ------

    """

    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering


        """
        current_speed = boid.velocity.length()

        # limit speed to a minimal value
        # speed can't be 0

        if current_speed < 0.0001:
            current_speed = 0.0001

        slowing_distance = (current_speed / boid.max_acceleration) * (current_speed / 2)

        # target offset is teh distance between current position and
        # destination
        target_offset = boid.destination - boid.position
        distance = target_offset.length()

        ramped_speed = boid.desired_speed * (distance / slowing_distance)
        clipped_speed = min(ramped_speed, boid.desired_speed)
        desired_velocity = (clipped_speed / distance) * target_offset

        steering = desired_velocity - boid.velocity

        if distance < boid.radius:
            boid.arrived = True

        return steering

class Wander:
    """ Class Wander

    Methods
    -------

    calculate

    """
    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering


        """
        wander_value = getattr(boid, 'wander_value', 0.0) + uniform(-0.5, 0.5)
        if wander_value < -2:
            wander_value = -2
        elif wander_value > 2:
            wander_value = 2
        boid.wander_value = wander_value
        desired_velocity = (boid.localy.scale(8) + boid.localx.scale(wander_value)).normalize() * boid.desired_speed
        steering = desired_velocity - boid.velocity
        return steering


class FollowWaypoints:
    """ Class FollowWaypoints

    Methods
    -------

    calculate

    """
    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering

        """

        waypoints = boid.waypoints
        if len(waypoints) == 0:
            boid.arrived = True
            return vec3()
        displacement = waypoints[0] - boid.position
        if displacement.length() < 2:
            del waypoints[0]
        desired_velocity = displacement.normalize() * boid.desired_speed
        steering = desired_velocity - boid.velocity
        return steering

class Separation:
    """ Class Separation

    """
    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering

        """


        the_world = boid.world
        others = the_world.boids(boid, 6.0)
        separation_distance = 6.0 * boid.velocity.length() / boid.max_speed
        acceleration = vec3()
        for other in others:
            local_position = the_world.to_local(boid, other.position)
            in_front = local_position[1] > -boid.radius
            if in_front and local_position.length() < separation_distance:
                separation = other.position - boid.position
                force = separation.scale(-1 / max(1e-9,separation.length() ** 2))
                # create orthogonal vector in order to make boids avoidance
                force2 = (-1**randint(0,1))*vec3(-force[1],force[0],0)
#                force2 = vec3(-force[1],force[0],0)
                acceleration += 0.5*force2 #3*force2
        return acceleration

class Queuing:
    """ Class Queuing

    """
    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering

        """

        the_world = boid.world
        others = the_world.boids(boid, 4)
        speed = boid.velocity.length()
        local_front = vec3(0,1)
        for other in others:
            local_position = the_world.to_local(boid, other.position)
            angle = local_position.angle(local_front)
            if local_position[1] > 0 and angle < pi / 8:
                if other.velocity.length() < speed:
                    return -boid.localy.scale(speed / boid.max_speed)
        return vec3()

# class Containment:
#     """ Class Containment 

#     """

#     def calculate(self, boid):
#         """ calculate boid behavior

#         Parameters
#         ----------

#         boid

#         Returns
#         -------

#         steering

#         """

#         the_world = boid.world
#         walls = the_world.obstacles(boid)
#         acceleration = vec3()
#         front_intersect = left_intersect = right_intersect = False
#         front_distance = left_distance = right_distance = 30000
#         speed = boid.velocity.length()
#         front_check = FCHK + speed * 0.5
#         side_check = SCHK + speed * 0.5
#         front_test = boid.localy.scale(front_check)
#         left_test = (boid.localy - boid.localx).scale(side_check)
#         right_test = (boid.localy + boid.localx).scale(side_check)
#         position = boid.position
#         boid.intersection = None
#         checked = []
#         df = FCHK+0.5
#         dl = SCHK
#         dr = SCHK
#         for wall in walls:
#             if wall in checked: continue
#             checked.append(wall)
#             intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, front_test,method = 'gauss')
#             if df > distance_along_check:
#                 df = distance_along_check
#                 if intersect and distance_along_check < front_distance:
#                     front_intersect = True
#                     front_distance = distance_along_check
#                     front_direction = direction
#             intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, left_test,method = 'direct')
#             if dl > distance_along_check:
#                 dl = distance_along_check
#                 if not front_intersect and intersect and distance_along_check < left_distance:
#                     left_intersect = True
#                     left_distance = distance_along_check
#                     left_direction = direction
#             intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, right_test,method = 'direct')
#             if dr > distance_along_check:
#                 dr = distance_along_check
#                 if not front_intersect and intersect and distance_along_check < right_distance:
#                     right_intersect = True
#                     right_distance = distance_along_check
#                     right_direction = direction
#             # if front_intersect or left_intersect or right_intersect :
#             #     break



# #    print speed
# #    # parabolic speed 
#         d_no_influ = 1.0#0.3 # m
#         repuls     = boid.velocity.length() #/ boid.max_speed
# #        speed = (repuls/(d_no_influ**2)*min(distance_along_check,d_no_influ)**2 - 2*repuls/(d_no_influ)*min(distance_along_check,d_no_influ) + repuls) #/ boid.max_speed
# #        speed = max (1.2*boid.max_speed, 1.0/(sqrt(2*pi*d_no_influ**2))*exp(-repuls**2/(2**d_no_influ**2)))
#         speed = max (boid.max_speed, d_no_influ/max(0.0001,(1.*repuls)))
#         speed = boid.velocity.length() / boid.max_speed # ORIGINAL CODE
#         # sf = max (boid.max_speed, speed*d_no_influ/max(0.0001,(1.*df)))
#         # sl = max (boid.max_speed, speed*d_no_influ/max(0.0001,(1.*dl)))
#         # sr = max (boid.max_speed, speed*d_no_influ/max(0.0001,(1.*dr)))
#         sf = 1 / max(df**2,1e-9)
#         sl = 1 / max(dl**2,1e-9)
#         sr = 1 / max(dr**2,1e-9)
#         acceleration = vec3()
#         if front_intersect:
#             if front_direction == 'left':
#                 acceleration = boid.localx.scale(sl) 
#                 acceleration = -boid.localy.scale(sf) 
#             else:
#                 acceleration = boid.localx.scale(sr) 
#                 acceleration = -boid.localy.scale(sf) 
#         # if left_intersect:
#         #     acceleration = boid.localx.scale(sl)
#         # if right_intersect:
#         #     acceleration = boid.localx.scale(sr)
        

#         return acceleration

#         # if front_intersect:
#         #     if front_direction == 'left':
#         #         acceleration = boid.localx.scale(speed) 
#         #     else:
#         #         acceleration = -boid.localx.scale(speed) 
#         # elif left_intersect:
#         #     acceleration = boid.localx.scale(speed)
#         # elif right_intersect:
#         #     acceleration = -boid.localx.scale(speed)
#         # else:
#         #     acceleration = vec3()

#         # return acceleration



class Containment:
    """ Class Containment 

    """

    def calculate(self, boid):
        """ calculate boid behavior

        Parameters
        ----------

        boid

        Returns
        -------

        steering

        """

        the_world = boid.world
        walls = the_world.obstacles(boid)
        acceleration = vec3()
        front_intersect = left_intersect = right_intersect = False
        front_distance = left_distance = right_distance = 10
        speed = boid.velocity.length()
        front_check = FCHK + speed * 0.5
        side_check = SCHK + speed * 0.5
        front_test = boid.localy.scale(front_check)
        left_test = (boid.localy - boid.localx).scale(side_check)
        right_test = (boid.localy + boid.localx).scale(side_check)
        position = boid.position
        boid.intersection = None
        checked = []
        df = FCHK+0.5
        dl = SCHK
        dr = SCHK
        acceleration = vec3()
        for wall in walls:
            # if wall in checked: continue
            # checked.append(wall)
            intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, front_test,method = 'direct')

            if intersect:
                if df > distance_along_check:
                    df = distance_along_check
                    if intersect and distance_along_check < front_distance:
                        front_intersect = True
                        front_distance = distance_along_check
                        front_direction = direction
            # intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, left_test,method = 'direct')
            # if intersect:
            #     if dl > distance_along_check:
            #         dl = distance_along_check
            #         if not front_intersect and intersect and distance_along_check < left_distance:
            #             left_intersect = True
            #             left_distance = distance_along_check
            #             left_direction = direction
            # intersect, distance_along_check, direction = self.test_intersection(boid, wall, position, right_test,method = 'direct')
            # if intersect:
            #     if dr > distance_along_check:
            #         dr = distance_along_check
            #         if not front_intersect and intersect and distance_along_check < right_distance:
            #             right_intersect = True
            #             right_distance = distance_along_check
            #             right_direction = direction
            # if front_intersect or left_intersect or right_intersect :
            #     break



# #    print speed
            
        if front_intersect:
            sf = 1 / max(front_distance**2,1e-9)

            if front_direction == 'left':
                acceleration += -vec3(boid.localy.scale(sf).tolist()) 
                acceleration += vec3(boid.localx.scale(sf).tolist() )

            else:

                acceleration += -vec3(boid.localy.scale(sf).tolist() )
                acceleration += -vec3(boid.localx.scale(sf).tolist() )
                # acceleration += boid.localx.scale(sr) 
        # if left_intersect:
        #     sl = 1 / max(sqrt(left_distance),1e-9)
        #     acceleration += boid.localx.scale(sl) 
        # if right_intersect:
        #     sr = 1 / max(sqrt(right_distance),1e-9)
        #     acceleration += -boid.localx.scale(sr) 

        return acceleration




#    def test_intersection(self, boid, wall, position, vector):
#        # From http://astronomy.swin.edu.au/~pbourke/geometry/lineline2d/
#        point1, point2 = wall
#        denominator = ((vector.y * (point2[0] - point1[0]))
#                       - (vector.x * (point2[1] - point1[1])))
#        if denominator == 0.0:
#            # parallel or coincident
#             return False, None, None
#        u_a = (vector.x * (point1[1] - position.y)
#               - (vector.y) * (point1[0] - position.x)) / denominator
#        u_b = ((point2[0] - point1[0]) * (point1[1] - position.y)
#               - (point2[1] - point1[1]) * (point1[0] - position.x)) / denominator
#        intersect = 0.0 < u_a < 1.0 and 0.0 < u_b < 1.0
#        if intersect:
#            intersection = vec3(point1[0] + u_a * (point2[0] - point1[0]),
#                                point1[1] + u_a * (point2[1] - point1[1]))
#            boid.intersection = intersection
#            distance_along_check = u_b
#            wall_vector = vec3(point1) - vec3(point2)
#            wall_vector_normal = vec3(-wall_vector.y, wall_vector.x).normalize()
#            boid.intersection_normal = wall_vector_normal
#            normal_point = intersection + wall_vector_normal
#            local_normal_point = boid.world.to_local(boid, normal_point)
#            if local_normal_point.x <= 0.0:
#                direction = 'left'
#            else:
#                direction = 'right'
#            return True, distance_along_check, direction
#        else:
#            return False, None, None

    def test_intersection(self, boid, wall, position, vector, method = 'direct'):
        """ test intersection

        Parameters
        ----------

        boid
        wall
        position
        vector
        method : string
            'direct' | 'gauss' | 'ellipse' | 'uniform'

        References
        ----------

        http://astronomy.swin.edu.au/~pbourke/geometry/lineline2d/

        """
        # From http://astronomy.swin.edu.au/~pbourke/geometry/lineline2d/
        point1, point2 = wall
        if method == 'direct':
            VR=vector
        elif method == 'uniform':
    ######## uniform version 
            r=uniform(-pi/12.0,pi/12.0)
            v0=vector.ang0()
            vl=vector.length()
            VR = vec3(cos(v0+r)*vl,sin(v0+r)*vl,vector.z)
        elif method == 'gauss':
    ######## gaussian version 
            vl=vector.length()
            r=gauss(vector.ang0(),pi/12.0)
            VR = vec3(cos(r)*vl,sin(r)*vl,vector.z)
        elif method == 'ellipse':
    ######## ellipse vesrion
            theta = gauss(vector.ang0(),sqrt(pi/6.0)) # random angle to test
            a = vector.length()                 # create an elipse... 
            b = a/1.5                            # ...to test  collision if b=a/1. ellipse =circle
            e = (sqrt(a**2-b**2))/a             # ...
            r = (b**2/a)/(1.0+e*cos(theta))     # ....
            VR = vec3(cos(theta)*r,sin(theta)*r,vector.z)
        denominator = ((VR.y * (point2[0] - point1[0]))
                    - (VR.x * (point2[1] - point1[1])))
        if denominator == 0.0:
            # parallel or coincident
            return False, 0.0, None
        u_a = (VR.x * (point1[1] - position.y)
               - (VR.y) * (point1[0] - position.x)) / denominator
        u_b = ((point2[0] - point1[0]) * (point1[1] - position.y)
               - (point2[1] - point1[1]) * (point1[0] - position.x)) / denominator
        intersect = 0.0 < u_a < 1.0 and 0.0 < u_b < 1.0
        if intersect:
            intersection = vec3(point1[0] + u_a * (point2[0] - point1[0]),
                                point1[1] + u_a * (point2[1] - point1[1]))
            boid.intersection = intersection
            distance_along_check = u_b
            wall_VR = vec3(point1) - vec3(point2)
            wall_VR_normal = vec3(-wall_VR.y, wall_VR.x).normalize()
            boid.intersection_normal = wall_VR_normal
            normal_point = intersection + wall_VR_normal
            local_normal_point = boid.world.to_local(boid, normal_point)
            if local_normal_point.x <= 0.0:
                direction = 'left'
            else:
                direction = 'right'
            return True, distance_along_check, direction
        else:
            return False, 0.0, None

class InterpenetrationConstraint:
    """ Class InterpenetrationConstaint

    """
    def calculate(self, boid):
        the_world = boid.world
        position = boid.position
        radius = boid.radius
        for other in the_world.boids(boid):
            offset = position - other.position
            distance = offset.length()
            radius_ij = radius + other.radius
            if distance < radius_ij:
                offset = offset.scale(radius_ij - distance)
                boid.position += offset
        wall_found = False
        checked = []
        for obstacle in the_world.obstacles(boid):
            if obstacle in checked: continue
            checked.append(obstacle)
            intersect, distance_to_line, normal = self.distance_from_line(position, obstacle)
            if intersect and distance_to_line < radius:
                wall_found = True
                normal = normal.scale(radius - distance_to_line)
                boid.position += normal
        if not wall_found:
            checked = []
            for obstacle in the_world.obstacles(boid):
                if obstacle in checked: continue
                checked.append(obstacle)
                for point in (obstacle[0], obstacle[1]):
                    offset = position - vec3(point)
                    distance = offset.length()
                    if distance < radius:
                        boid.position += offset.scale(radius - distance)
    # if intersect and distance_to_line < radius * 1.2:
    #             wall_found = True
    #             normal = normal.scale(radius * 1.2 - distance_to_line)
    #             boid.position += normal
    #     if not wall_found:
    #         checked = []
    #         for obstacle in the_world.obstacles(boid):
    #             if obstacle in checked: continue
    #             checked.append(obstacle)
    #             for point in (obstacle[0], obstacle[1]):
    #                 offset = position - vec3(point)
    #                 distance = offset.length()
    #                 if distance < radius * 1.2:
    #                     boid.position += offset.scale(radius * 1.2 - distance)

        return vec3()

    def distance_from_line(self, position, line):
        """ distance from line

        Parameters
        ----------

        position : 2D vector
        line : np.array

        Returns
        -------

        True , distance , vector
        or 
        False , None , None 

        """
        line_length = (vec3(line[1]) - vec3(line[0])).length()
        u = ((position.x - line[0][0]) * (line[1][0] - line[0][0])
           + (position.y - line[0][1]) * (line[1][1] - line[0][1])) \
            / line_length ** 2
        if 0.0 < u < 1.0:
            # point is tangent to line
            x = line[0][0] + u * (line[1][0] - line[0][0])
            y = line[0][1] + u * (line[1][1] - line[0][1])
            vector = position - vec3(x, y)
            distance = vector.length()
            return True, distance, vector
        return False, None, None

def default_steering_mind(boid):
    """ Sum all steering vectors.

    Parameters
    ----------

    boid

    Notes
    -----

    This is the place where all acceleration from all behaviors are summed.

    """

    acceleration = vec3()
    for behavior in boid.behaviors:
        acceleration += behavior.calculate(boid)
    return acceleration

def queue_steering_mind(boid):
    """Sum of all steering vectors, except Separation in some cases.

    The Separation steering vector will be ignored if any prior
    steering behavior gave a non-zero acceleration, typically
    Containment.

    """

    acceleration = vec3()
    for behavior in boid.behaviors:
#        if not isinstance(behavior, Separation) or acceleration.length() < 0.0001:
         acceleration += behavior.calculate(boid)
    return acceleration
