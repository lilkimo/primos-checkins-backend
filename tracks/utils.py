from datetime import date, datetime, timedelta
from re import findall, fullmatch
from tracks import parameters

# Esta función es importante para el debug, ya que nos
# permite cambiar fácilmente la hora en toda la app.
def now():
    return datetime.now()#.replace(day=9, hour=9, minute=26, second=0, microsecond=0)

def firstWeekday(reference: datetime = now()):
    return reference.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days = reference.weekday())

def firstMonthDay(month: int, year: int = now().year):
    return date(year, month, 1)

def getRegex():
    lastShift = len(parameters.shifts) - 1
    return f'([{parameters.days}](?:[0-{lastShift}],)*[0-{lastShift}])'

def verifyRegex(schedule: str) -> bool:
    return fullmatch(f'{getRegex()}+', schedule) != None

# Retorna el horario del primo, ordenado desde el turno actual (desde el punto de
# referencia <reference>) o el más cercano, hasta el más lejano.
def parseSchedule(schedule: str, reference = now()):
    nextWeek = timedelta(days=7)
    shifts = []
    
    for daily in findall(getRegex(), schedule):
        for i in daily[1:].split(','):
            shift = parameters.shifts[int(i)]
            checkout = firstWeekday(reference).replace(hour=shift[2][0], minute=shift[2][1]) + timedelta(parameters.days.index(daily[0]))
            # Si el turno de esta semana ya terminó, entonces lo tiro para la
            # próxima semana
            if checkout < reference:
                checkout += nextWeek
            checkin = checkout.replace(hour=shift[1][0], minute=shift[1][1])
            shifts.append({
                "block": shift[0],
                "checkin": checkin,
                "checkout": checkout
            })
    
    shifts.sort(key=lambda s: s["checkin"])
    return shifts

# Esta función, dado <date: datetime> (Fecha y hora), retornará el bloque al que
# pertenece la hora proporcionada (Si esta está dentro de los límites del bloque)
# o el bloque más cercano. Es importante recalcar que encontrará el bloque más
# cercano dentro del día de la semana indicado. Por ejemplo; si nos encontramos
# el día Martes a las 23:00, nos retornaría el Martes 1-2 de la semana siguiente
# o un error (Véase el parámetro <strinctmode>).
# <strictmode: bool>: 
#   False: Se aproxima al bloque más cercano dentro del día de la semana indicado,
#    independiente de cuanto tiempo falte para ese bloque (Podrían ser desde
#    minutos, horas o incluso semanas).
#   True: Se aproxima al bloque más cercano dentro del día de la semana indicado
#    sólo si estamos dentro de los límites de la tolerancia; si falta mucho para
#    que comience el bloque o es demasiado tarde, lanzará un error.
def aproximateToBlock(date: datetime, strictmode = True):
    firstHour = date.replace(hour=0, minute=0, second=0, microsecond=0)
    if (weekday := firstHour.weekday()) > 4:
        if strictmode:
            raise Exception(f'<date> ({date}) is not a weekday, so is not close enough to any block')
        firstHour += timedelta(days=7 - weekday)
    
    for shift in parameters.shifts:
        checkin = firstHour.replace(hour=shift[1][0], minute=shift[1][1])
        checkout = firstHour.replace(hour=shift[2][0], minute=shift[2][1])

        if strictmode:
            # Aproxima al siguiente bloque más cercano sólo si estamos dentro del
            # tiempo de tolerancia
            nextblockCondition = checkin - parameters.beforeStartTolerance < date < checkin # <=
        else:
            # Aproxima directamente al bloque más cercano
            nextblockCondition = date < checkin

        if (checkin <= date <= checkout) or nextblockCondition:
            return {
                "block": shift[0],
                "checkin": checkin,
                "checkout": checkout
            }
    if strictmode:
        raise Exception(f'<date> ({date}) is not close enough to any block')
    
    nextWeek = timedelta(days=7)
    shift = parameters.shifts[0]
    return {
        "block": shift[0],
        "checkin": checkin + nextWeek,
        "checkout": checkout  + nextWeek
    }

def upcomingShift():
    return aproximateToBlock(now(), False)