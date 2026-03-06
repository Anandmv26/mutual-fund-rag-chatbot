import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import App from '../App'
import axios from 'axios'

// Mock smooth scrollIntoView which is missing in jsdom
window.HTMLElement.prototype.scrollIntoView = function () { };

vi.mock('axios')

describe('WealthWise AI App', () => {
    it('renders header correctly', async () => {
        axios.get.mockImplementation((url) => {
            if (url.includes('/suggestions')) return Promise.resolve({ data: { suggestions: ["Sug 1", "Sug 2", "Sug 3"] } })
            if (url.includes('/supported-funds')) return Promise.resolve({ data: { funds: ["Fund A", "Fund B"] } })
            return Promise.resolve({ data: {} })
        })
        render(<App />)
        expect(screen.getByText('WealthWise AI')).toBeInTheDocument()
        expect(screen.getByText('Your Gateway to Institutional-Grade Financial Growth')).toBeInTheDocument()
    })

    it('renders initial bot message', async () => {
        axios.get.mockImplementation((url) => {
            if (url.includes('/suggestions')) return Promise.resolve({ data: { suggestions: ["Sug 1", "Sug 2", "Sug 3"] } })
            if (url.includes('/supported-funds')) return Promise.resolve({ data: { funds: [] } })
            return Promise.resolve({ data: {} })
        })
        render(<App />)
        expect(screen.getByText(/Welcome to your premium investment suite/i)).toBeInTheDocument()
        expect(screen.getByText('VERIFIED FINANCIAL INTELLIGENCE')).toBeInTheDocument()
    })

    it('handles sending a message and receiving a response', async () => {
        axios.get.mockImplementation((url) => {
            if (url.includes('/suggestions')) return Promise.resolve({ data: { suggestions: [] } })
            if (url.includes('/supported-funds')) return Promise.resolve({ data: { funds: [] } })
            return Promise.resolve({ data: {} })
        })
        axios.post.mockResolvedValue({
            data: {
                answer: 'A mutual fund gathers pooled money from investors.',
                source_url: 'https://example.com',
                suggestions: ['Show me DSP'],
                is_in_scope: true
            }
        })

        render(<App />)

        // Using getAllByRole to get the send button (the suggestions pills are also buttons)
        // Wait for the components to mount
        const input = await screen.findByPlaceholderText('Ask about funds, performance, or strategy...')
        fireEvent.change(input, { target: { value: 'What is a mutual fund?' } })

        // Identify send button specifically by sending a class query or just picking the last button
        const buttons = screen.getAllByRole('button')
        const sendButton = buttons[buttons.length - 1] // send button is at the bottom

        fireEvent.click(sendButton)

        expect(screen.getByText('What is a mutual fund?')).toBeInTheDocument()

        await waitFor(() => {
            expect(screen.getByText('A mutual fund gathers pooled money from investors.')).toBeInTheDocument()
        })
    })

    it('renders supported funds toggle and list', async () => {
        axios.get.mockImplementation((url) => {
            if (url.includes('/suggestions')) return Promise.resolve({ data: { suggestions: [] } })
            if (url.includes('/supported-funds')) return Promise.resolve({ data: { funds: ["Quant Small Cap Fund", "HDFC Infrastructure Fund"] } })
            return Promise.resolve({ data: {} })
        })

        render(<App />)

        // Wait for the toggle button to appear
        const toggleBtn = await screen.findByText('Supported Mutual Funds')
        expect(toggleBtn).toBeInTheDocument()

        // List should not be visible initially
        expect(screen.queryByText('Quant Small Cap Fund')).not.toBeInTheDocument()

        // Click to expand
        fireEvent.click(toggleBtn)

        // Items should now be visible
        await waitFor(() => {
            expect(screen.getByText('Quant Small Cap Fund')).toBeInTheDocument()
            expect(screen.getByText('HDFC Infrastructure Fund')).toBeInTheDocument()
        })
    })
})
