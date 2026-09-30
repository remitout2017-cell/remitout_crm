import { baseApi } from '../../store/baseApi'
import type { Student, StudentInput } from '../../types'

export const studentsApi = baseApi.injectEndpoints({
  endpoints: (b) => ({
    getStudents: b.query<Student[], void>({ query: () => '/students?limit=200', providesTags: ['Student'] }),
    getStudent: b.query<Student, number>({ query: (id) => `/students/${id}`, providesTags: (_r, _e, id) => [{ type: 'Student', id }] }),
    addStudent: b.mutation<Student, StudentInput>({
      query: (body) => ({ url: '/students', method: 'POST', body }),
      invalidatesTags: ['Student'],
    }),
    updateStudent: b.mutation<Student, { id: number; body: Partial<StudentInput> }>({
      query: ({ id, body }) => ({ url: `/students/${id}`, method: 'PATCH', body }),
      invalidatesTags: ['Student'],
    }),
  }),
})

export const { useGetStudentsQuery, useGetStudentQuery, useAddStudentMutation, useUpdateStudentMutation } = studentsApi
