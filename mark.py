import os, sys, time, codecs, subprocess as bash, signal, json

#----- set argument part -----

def load_json(fname, encoding = 'utf-8'):
    with open(fname) as f:
        return json.load(f, encoding)

conf = load_json('./config.json')

upload = conf["uploaded_directry"]
#uploaded directry format
#upload/q1/students' code
#      /q2/students' code
#      /q3/students' code
#      /q4/students' code
#      /q5/students' code

ID_list = conf["student_ID_list"]

ans_dir = conf["answer_directry"]

ws = conf["work_space"]
code = ws+'/code'
exe = ws+'/exe'
out = ws+'/out'

check_q = conf["check_question_number"]

entry = conf["input_value_to_program"]

          
#----- make environment -----
def make_qnum(q):
    return '/q'+str(q)

def set_Qnum(dir = '',q_num = range(1,6)):
    qnum_list =[]
    for i in map(make_qnum, q_num):
        qnum_list += [dir + i]
    return qnum_list

#MaKe Question DIRectry. => MKQDIR
def mkqdir(d):
    for q in set_Qnum(dir = d):
        bash.call(['mkdir',q])

#set environment:make the directries and copy students' answer code from the uploaded directry.
def set_env():
    bash.call(['mkdir',ws])
    bash.call(['mkdir',exe])
    bash.call(['mkdir',out])
    bash.call(['mkdir',code])
    mkqdir(exe)
    mkqdir(out)
    
    bash.call('cp -r '+upload+'/q* '+code,shell =True)
       
    os.chdir(ws)

#----- definition part -----

class Student:
    def __init__(self, id):
        self.id = id
        self.score = ''

    def show(self):
        return  self.id+','+self.score

def compile(student, exe, code, log):
    return bash.Popen(['gcc','-o',exe+'/'+student.id,code+'/'+student.id+'.c',
                       '-lm'], stdout = log, stderr = bash.STDOUT)
    
def run(student, exe, out, log, entry = ''):
    return bash.Popen(exe+'/'+student.id+' '+entry+' > '+out+'/'+student.id+'.txt', stdout = log, stderr = bash.STDOUT, shell = True, preexec_fn=os.setsid)

def compile_isOK(student,q, log = sys.stderr):
        compile_ps = compile(student, exe+q,code+q,log)
        compile_ps.wait()
        if not os.path.isfile(exe+q+'/'+student.id):
            return False
        else :
            return True

def isLoop(student, q, log = sys.stderr, entry = ''):
    run_ps = run(student, exe+q, out+q, log, entry)
    time.sleep(0.3)
    if run_ps.poll() is None:
        os.killpg(run_ps.pid,signal.SIGTERM)
        return True
    else:
        return False

def isAttend(student, q):
    if os.path.isfile(code+q+'/'+student.id+'.c'):
        return True
    else:
        return False

#check is a function checking that students' answer is OK or not.
#This function must takes two file objects and Student instance as arguments.
#If right answer is different for each students,
#programmer can make different check function and set to check_func list.
def check(st, answer, st_out):
    return answer == st_out

def ans_check(student, q, check , ans):
    st_out = codecs.open(out+q+'/'+student.id+'.txt', 'r', 'utf-8').read()
    if check(student, ans, st_out) :
        student.score = '20'
    else:
        student.score = '0'


def q_check(students, q, entry, ans, check):
    result = open(ws+q+'_result.csv', 'w')
    log = open(ws+q+'_log.txt', 'w')
    for st in students:
#        print st.id+'\'s check start\n'
        log.write(st.id+'\'s check start\n')
        log.flush()
        os.fsync(log.fileno())
        if not isAttend(st, q):
            st.score = 'Absence'
            result.write(st.show()+'\n')
            log.write(st.id+' is Absence\n'+st.id+'\'s check end\n\n\n')
            continue
        if not compile_isOK(st, q, log):
            st.score = 'Compile error'
            result.write(st.show()+'\n')
            log.write(st.id+'\'s check end\n\n\n')
            continue
        if isLoop(st, q, log, entry):
            st.score = 'Time out'
            log.write(st.id+' is Time out\n')
        else:
            ans_check(st, q, check, ans)
        log.write(st.id+'\'s check end\n\n\n')
        result.write(st.show()+'\n')
    result.close()
    log.close()


def all_check(students, entry, check_func, q_num):
    for q in q_num:
        print "start check ",q[1:]
        print 'entry[',q[1:],'] = ',entry[q[1:]]
        ans = codecs.open(ans_dir+q+'.txt', 'r', 'utf-8').read()
        q_check(students, q, entry[q[1:]], ans,check_func[int(q[2:]) - 1])
        print "check end ",q[1:]

def mark2(id_list, check_q, entry, check_func):
    students = []
    q_num = set_Qnum(q_num = check_q)
    for id in id_list:
        students += [Student(id)]
    all_check(students, entry, check_func, q_num)


#----- run part -----
#set_env()

#check_func list has functions to check that q1-q5 is OK.
check_func = [check,check,check,check,check]

students = open(ID_list,'r').read().split()

mark2(students, check_q, entry, check_func)

