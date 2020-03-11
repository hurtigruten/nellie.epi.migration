const express = require('express')
const bodyParser = require('body-parser')
const TurndownService = require('turndown')
const { richTextFromMarkdown } = require('@contentful/rich-text-from-markdown')
const asyncHandler = require('express-async-handler')
const app = express()

const turndownService = new TurndownService()

const htmlToMarkdown = (html) => {
    return turndownService.turndown(html).replace(/\*\*\*\*/g, '**')
}

const markdownToRichtext = (markdown) => {
    return richTextFromMarkdown(markdown)
}

const htmlToRichText = (html) => {
    return markdownToRichtext(htmlToMarkdown(html))
}

app.use(bodyParser.json())

app.post('/convert', asyncHandler(async (req, res, next) => {

    const from = req.body.from
    const to = req.body.to
    const markdown = req.body.markdown
    const html = req.body.html.replace(/<a.*href="(.*?)".*>(.*?)<\/a>/gi, "$2")

    switch (from) {
        case 'html':
            
            if (html === undefined) {
                throw new Error('Please specify a value for "html" in your body')
            }

            switch (to) {
                case 'markdown':
                    res.send(htmlToMarkdown(html))
                    break
                case 'richtext':
                    const richtext = await htmlToRichText(html)
                    res.send(richtext)    
                    break
                default:
                    throw new Error('Please specify "to" value as "markdown" or "richtext"')
            }

            break

        case 'markdown':

            if (markdown === undefined) {
                throw new Error('Please specify a value for "markdown" in your body')
            }

            switch (to) {
                case 'markdown': 
                    res.send(markdown)
                    break
                case 'richtext':
                    const richtext = await richTextFromMarkdown(markdown)
                    res.send(richtext)    
                    break
                default:
                    throw new Error('Please specify "to" value as "markdown" or "richtext"')
            }

            break

        default: 
            
            throw new Error('Please specify "from" value as "html" or "markdown"')
    }
}))

app.listen(3000, 'localhost')